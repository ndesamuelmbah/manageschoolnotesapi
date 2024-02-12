import traceback
import firebase_admin
from firebase_admin import firestore, credentials, messaging, storage, auth
from firebase_admin.auth import create_user, delete_user, update_user, get_user, get_users, UserIdentifier, UidIdentifier, UserInfo, UserProvider, UserRecord, ListUsersPage
from firebase_admin._user_mgt import ProviderUserInfo
from typing import Optional, List, Dict
from fastapi import FastAPI, File, UploadFile, Form, Depends, Security, Query, Body, Path, BackgroundTasks, status, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware

from pydantic import EmailStr, BaseModel, HttpUrl
from models import OrderedMenuItems, RestaurantMenuItem


import os, io, re, json , unidecode, pytz
from time import time, sleep
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK with your service account credentials

cred = credentials.Certificate('/app/service_account_creds_manageschoolnotes.json')#publishing to gc
#cred = credentials.Certificate('C:/Users/samund/source/service_account_creds_manageschoolnotes.json')#Local debugging
firebase_admin.initialize_app(cred,  options = {"storageBucket": 'manageschoolnotes.appspot.com' })
firestoreDB = firestore.Client(project='manageschoolnotes')

timezone = pytz.timezone('US/Pacific')

app = FastAPI()

#set up CORS support.
origins = (os.environ.get('ALLOWED_ORIGINS') or '').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_DOMAIN = os.environ.get('EMAIL_DOMAIN')


@app.get("/")
async def home():
    return {'success': 'You are now seeing the hello world of this project. Everything is working well.'}

def get_cameroon_time_now(in_millisecs = False):
    time_now = datetime.utcnow() + timedelta(hours = 1)
    if(in_millisecs):
        return int(time_now.timestamp()*1000)
    return time_now

def get_formatted_user_map(user):
    user_data = {
            'uid': user.uid,
            'email': user.email,
            'emailVerified': user.email_verified,
            'displayName': user.display_name,
            'photoUrl': user.photo_url,
            'disabled': user.disabled,
            'phoneNumber': user.phone_number,
            'customClaims': user.custom_claims,
            'tenantId': user.tenant_id,
            'creationTime': user.user_metadata.creation_timestamp or int(get_cameroon_time_now().timestamp() * 1000),
            'providers': [{'uid': providerInfo.uid,
                           'displayName': providerInfo.display_name,
                           'email': providerInfo.email,
                           'phoneNumber': providerInfo.phone_number,
                           'photoUrl': providerInfo.photo_url,
                           'providerId': providerInfo.provider_id} for providerInfo in user.provider_data]
        }
    return user_data

@app.post("/receive_emails")
async def receive_emails(request: Request):
    data = await request.json()
    # Assuming the email data is in the format received from AWS WorkMail
    sender = data['sender']
    subject = data['subject']
    body = data['body']
    # Additional data processing or validation as per your requirements

    # Save the email data to Firestore
    emailData = {
        'sender': sender,
        'subject': subject,
        'body': body,
        'host': request.client.host,
        'url': str(request.url),
        'base_url': str(request.base_url),
        'headers': dict(request.headers),
        'rawEmail': data
    }
    doc_ref = firestoreDB.collection('receivedEmails').document()
    doc_ref.set(emailData)
    return emailData

@app.post("/receive_raw_emails")
async def receive_raw_emails(request: Request):
    emailData = await request.json()
    # Additional data processing or validation as per your requirements

    # Save the email data to Firestore
    emailData['host'] = request.client.host,
    emailData['url'] = str(request.url),
    emailData['base_url'] = str(request.base_url),
    emailData['headers'] = dict(request.headers),
    doc_ref = firestoreDB.collection('receivedEmails').document(str(get_cameroon_time_now()))
    doc_ref.set(emailData)
    return emailData

# @app.post("/charge_ussd_webhooks_live/")
# async def charge_ussd_webhooks_live(request: Request,
#     background_tasks: BackgroundTasks):
#     body = {}
#     try:
#         body = await request.json()
#         print(body)
#         if 'data' in body:
#             res = body['data']
#             for key in ['event', 'reason']:
#                 if key in body:
#                     res[key] = body[key]
#     except:
#         pass
#     host = request.client.host
#     isValidHost = host in PAYSTACK_USSD_HOST
#     params = {'isValidHost': isValidHost, 'host': host, 'url': str(request.url), 'base_url': str(request.base_url), 'headers': dict(request.headers)}
#     body.update(params)
#     if 'reference' in body:
#         background_tasks.add_task(addPaymentForOrder, reference=body['reference'], details=body)
#     return body

# @app.post("/stripe_webhook")
# async def stripe_webhook(request: Request,
#     background_tasks: BackgroundTasks):
#     body = {}
#     try:
#         body = await request.json()
#         if 'data' in body and type(body['data']) == dict:
#             res = body['data']
#             res = {k: v for k, v in res if v is not None}
#             for k, v in body.items():
#                 if k != 'data' and v is not None:
#                     if k not in res:
#                         res[k] = v
#                     else:
#                         res[f'top_{k}'] = v
#             body = res
#             for key in ['event', 'reason']:
#                 if key not in body:
#                     body[key] = 'Waiting for Payment'
#     except:
#         pass
#     host = request.client.host
#     isValidHost = host in PAYSTACK_USSD_HOST
#     params = {'isValidHost': isValidHost, 'host': host, 'url': str(request.url), 'base_url': str(request.base_url), 'headers': dict(request.headers)}
#     body.update(params)
#     body = {k: v for k, v in body if v is not None}
#     if 'id' in body:
#         body['reference'] = body['id']
#     if 'reference' in body:
#         body['dataSource'] = 'stripe'
#         background_tasks.add_task(addPaymentForOrder, reference=body['reference'], details=body)
#     return body


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = auth.get_user(user_id)
        return get_formatted_user_map(user)
    except Exception as e:
        return {'message': str(e)}

@app.get("/see_env_vars/{requested_by}")
async def see_env_vars(
    requested_by: str = Path(..., min_length=5, max_length=40)):
    who_can_see = os.environ.get('WHO_CAN_SEE_ENV_VARS')
    who_can_see = who_can_see.split('|') if who_can_see is not None else []
    if(requested_by in who_can_see):
        return os.environ
    return {'Opps': 'Are you sure you have access? We are watching you.'}

@app.get("/ping_api/{uid}")
async def ping_api(
    uid: str = Path(..., min_length=5, max_length=40)):
    try:
        user = auth.get_user(uid)
        return get_formatted_user_map(user)
    except Exception as e:
        return {'failure': f"No User Exists with the provided user id uid == {uid}", 'exception': f'Exception({e})'}

@app.get("/notify_email_verification/{uid}/{timeStamp}")
async def notify_email_verification(
    uid: str = Path(..., min_length=5, max_length=40),
    timeStamp: int = Path(..., ge=10000000)):
    firestoreDB.collection('pendingAuthentications').document(str(timeStamp)).set({
                                'isSignedIn': True,
                                'timeStamp': timeStamp,
                                'uid': uid
    })
    sleep(2)
    return {'Status': 'Success', 'Reason': 'Your Email has been successfully updated'}

@app.get("/link_user_with_password/{uid}/{new_email}/{password}/{time_stamp}")
async def link_user_with_password(
    uid: str = Path(..., min_length=5, max_length=40),
    new_email: EmailStr = Path(...),
    password: str = Path(..., max_length=60, min_length=8),
    time_stamp: int = Path(..., ge=10000000)):
    auth.update_user(uid, email=new_email, email_verified=True, password = password)
    updated_user = get_formatted_user_map(auth.get_user(uid=uid))
    updates = {'providers': updated_user['providers']}
    user_ref = firestoreDB.collection("customers").document(uid)
    user_ref.update(updates)
    return {'Status': 'Success', 'Reason': 'Your Email has been successfully updated'}


def get_user_by_email(email: str):
    try:
        user = auth.get_user_by_email(email)
        return user
    except Exception as e:
        return {'message': str(e)}

def get_user_by_phone(phone_number):
    user_snapshot = firestoreDB.collection("customers").document(phone_number).get()
    user = user_snapshot.to_dict()
    print(f'Getting User by email response is {user}')
    return user

@app.get("/current_exchange_rates")
async def current_exchange_rates():
    rates = firestoreDB.collection("exchangeRates").document('currentRates').get()
    return rates.to_dict()

@app.get("/fix_over_written_user")
async def fix_over_written_user():
    user = get_user_by_email(email='ndesamuelmbah@gmail.com')
    fuser = get_formatted_user_map(user)
    user_ref = firestoreDB.collection("customers").document('+13016408856')
    user_ref.update(fuser)
    updated_user = user_ref.get()
    return updated_user.to_dict()

def create_new_user(uid,
                    email,
                    phone_number,
                    display_name,
                    email_verified,
                    custom_claims,
                    is_admin,
                    timestamp):
    new_user = create_user(uid = uid,
                        email = email or f"msn-{timestamp}@{EMAIL_DOMAIN}.com",
                        password = EMAIL_PASSWORD,
                        phone_number = phone_number,
                        display_name = display_name,
                        email_verified=email_verified)
    auth.set_custom_user_claims(uid=new_user.uid, custom_claims=custom_claims)

    formatted_user = get_formatted_user_map(new_user)
    formatted_user['isAdmin'] = is_admin
    formatted_user['customClaims'] = custom_claims
    try:
        firestoreDB.collection('customers').document(phone_number).set(formatted_user)
    except:
        firestoreDB.collection('customers').document(phone_number).update(formatted_user)
    return formatted_user

async def register_contact_messages(uid, user_name, phone_number, contact_message, email):
    now = int(get_cameroon_time_now().timestamp()*1000)
    if(contact_message is not None):
        data = {
            'uid': uid,
            'userName': user_name,
            'phoneNumber': phone_number,
            'contactMessage': contact_message,
            'email': email,
            'timestamp': now,
            'hasResponse': False
        }
        firestoreDB.collection('contactUs').document(str(now)).set(data)
        firestoreDB.collection('customers').document(phone_number).collection('contactUs').document(str(now)).set(data)

async def create_order(uid, user_name, phone_number, delivery_message, email, ordered_menu_items, time_now):
    now = int(time_now.timestamp()*1000)
    if(delivery_message is not None):
        total_price = 0
        for ordered_menu_item in ordered_menu_items:
            total_price += ordered_menu_item.quantity*ordered_menu_item.itemPrice

        data = {
            'uid': uid,
            'userName': user_name,
            'phoneNumber': phone_number,
            'deliveryMessage': delivery_message,
            'email': email,
            'timestamp': now,
            'orderId': str(now),
            'orderedDateTime': str(time_now),
            'lastUpdatedTime': now,
            'orderStatus': 'Order Placed',
            'modeOfPayment': 'TBD - Cash On Pickup',
            'orderStatusIndex': 0,
            'deliveryAddress': 'NA',
            'totalPrice': round(total_price, 2),
            'orderedMenuItems': [dict(ordered_menu_item) for ordered_menu_item in ordered_menu_items]
        }
        firestoreDB.collection('orders').document(str(now)).set(data)
        firestoreDB.collection('customers').document(phone_number).collection('orders').document(str(now)).set(data)
        firestoreDB.collection('customers').document(phone_number).update({'currentOrderId': str(now)})
        auth.set_custom_user_claims(uid, custom_claims={'isAdmin': False, 'currentOrderId': str(now)})
        print('Successfully created order and updated user')

async def update_firebase_user(uid, phone_number, email):
    now = int(get_cameroon_time_now().timestamp()*1000)
    data = {
        'uid': uid,
        'phoneNumber': phone_number,
        'email': email,
    }
    try:
        auth.update_user(uid, email=email)
        firestoreDB.collection('customers').document(phone_number).update(data)
    except Exception as e:
        data['exception' ]= str(e)
        data['source'] = 'update_firebase_user'
        firestoreDB.collection('adminLogs').document(str(now)).set(data)


@app.post("/update_user_claims")
async def update_user_claims(*,
    uid : str = Form(...),
    accountNumber : str = Form(..., min_length = 8, max_length = 15, regex="\d{13,14}$"),
    creationTime : int = Form(...),
    isAdmin: bool = Form(False),
    isExecutive: bool = Form(False),
    isRegisteredInNDY: bool = Form(False),
    background_tasks: BackgroundTasks):
    update_timestamp = get_cameroon_time_now(in_millisecs=True)
    custom_claims = {
          'isAdmin': isAdmin,
          'isExecutive': isExecutive,
          'isRegisteredInNDY': isRegisteredInNDY,
          'creationTime': creationTime,
          'accountNumber': accountNumber,
          'lastUpdatedTime': update_timestamp
        }
    updates = dict()
    updates.update(custom_claims)
    updates['customClaims'] = custom_claims
    firestoreDB.collection('customers').document(uid).update(updates)
    auth.set_custom_user_claims(uid=uid, custom_claims=custom_claims)
    return updates

@app.post("/update_order")
async def update_order(*,
    orderId : str = Form(..., min_length = 4, max_length = 35),
    newOrderStatus : str = Form(..., min_length=5, max_length=30),
    orderByPhone : str = Form(..., min_length = 8, max_length = 15, regex="\+?\d{8,14}$"),
    orderCancellationMessage : str = Form(None),
    isAdmin: bool = Form(...),
    background_tasks: BackgroundTasks):

    updates = {
        'orderStatus': newOrderStatus,
        'lastUpdatedTime': get_cameroon_time_now(in_millisecs=True),
        'isUpdatedByAdmin': isAdmin
    }
    custom_claims ={'isAdmin': False}
    update_date_time = str(get_cameroon_time_now())
    if orderCancellationMessage is not None:
        updates['orderCancellationMessage'] = orderCancellationMessage
    if('accept' in newOrderStatus.lower()):
        updates['orderStatusIndex'] = 1
    if('cancel' in newOrderStatus.lower()):
        updates['orderStatusIndex'] = 2
        updates['currentOrderId'] = None
        custom_claims['currentOrderId'] = None
        updates['cancellationDateTime'] = update_date_time
    elif('ready' in newOrderStatus.lower()):
        updates['orderStatusIndex'] = 3
    elif('delivered' in newOrderStatus.lower()):
        updates['orderStatusIndex'] = 4
        updates['currentOrderId'] = None
        custom_claims['currentOrderId'] = None
        updates['deliveryDateTime'] = update_date_time
    firestoreDB.collection('orders').document(orderId).update(updates)
    background_tasks.add_task(update_user_claims, uid=orderByPhone, custom_claims=custom_claims, phone_number=orderByPhone)
    updates['orderId'] = orderId
    updates.update(custom_claims)
    return updates

@app.post("/get_or_create_user")
async def get_or_create_user(*,
    userName : str = Form(..., min_length = 4, max_length = 35, regex="^[a-zA-Z]{2,}( [a-zA-Z]{2,}){1,3}$"),
    phoneNumber : str = Form(..., min_length = 8, max_length = 15, regex="\+?\d{8,14}$"),
    contactMessage : str = Form(None, min_length = 8),
    email : EmailStr = Form(None),
    emailVerified: bool = Form(True),
    isAdmin: bool = Form(False),
    skipFirestoreCheck: bool = Form(False),
    deliveryMessage: str = Form(None),
    orderedMenuItems : str = Form(None),
    background_tasks: BackgroundTasks):
    '''
    Creates a customer.
    Please only verify customers after they have been created.
    '''

    userName = userName.title()
    phoneNumber = '+' + phoneNumber.strip('+ ').replace(' ', '')
    orderedMenuItems = orderedMenuItems if orderedMenuItems is None else [RestaurantMenuItem(**item_dict) for item_dict in eval(orderedMenuItems)]
    if(email is not None):
        email = email.lower()
    try:
        time_now = get_cameroon_time_now()
        timestamp = int(time_now.timestamp()*1000)
        custom_claims={'isAdmin': isAdmin, 'createTimestamp': timestamp}
        email = email or f"msn-{timestamp}@{EMAIL_DOMAIN}.com"
        if(skipFirestoreCheck):
            new_user=  create_new_user(uid = phoneNumber,
                                    email = email,
                                    phone_number = phoneNumber,
                                    display_name = userName,
                                    email_verified=emailVerified,
                                    custom_claims = custom_claims,
                                    is_admin = isAdmin,
                                    timestamp = timestamp)
            if (contactMessage is not None):
                background_tasks.add_task(register_contact_messages, uid=phoneNumber, user_name = userName, phone_number = phoneNumber, contact_message = contactMessage, email = email)
            if (orderedMenuItems is not None and len(orderedMenuItems) > 0):
                background_tasks.add_task(create_order, uid=phoneNumber, user_name = userName, phone_number = phoneNumber, delivery_message = deliveryMessage, email = email, ordered_menu_items=orderedMenuItems, time_now = time_now)
                new_user['currentOrderId'] = str(timestamp)
            return new_user
        else:
            firestore_user = get_user_by_phone(phone_number=phoneNumber)
            print(firestore_user)
            if firestore_user is not None and len(firestore_user)> 1:
                auth_user = get_user_by_email(firestore_user['email'])
                if(auth_user.email != email and not email.endswith(f'@{EMAIL_DOMAIN}.com')):
                    background_tasks.add_task(update_firebase_user, uid = phoneNumber, phone_number = phoneNumber, email = email)
                if (contactMessage is not None):
                    background_tasks.add_task(register_contact_messages, uid = phoneNumber, user_name = userName, phone_number = phoneNumber, contact_message = contactMessage, email = auth_user.email)
                formatted_user = get_formatted_user_map(auth_user)
                if (orderedMenuItems is not None and len(orderedMenuItems) > 0):
                    prev_order_id = firestore_user.get('currentOrderId')
                    if prev_order_id is None or len(str(prev_order_id))< 3:
                        background_tasks.add_task(create_order, uid=phoneNumber, user_name = userName, phone_number = phoneNumber, delivery_message = deliveryMessage, email = auth_user.email, ordered_menu_items=orderedMenuItems, time_now = time_now)
                        formatted_user['currentOrderId'] = str(timestamp)
                return formatted_user
            else:
                new_user = create_new_user(uid = phoneNumber,
                                        email = email,
                                        phone_number = phoneNumber,
                                        display_name = userName,
                                        email_verified=emailVerified,
                                        custom_claims = custom_claims,
                                        is_admin = isAdmin,
                                        timestamp = timestamp)
                if (contactMessage is not None):
                    background_tasks.add_task(register_contact_messages,uid = phoneNumber, user_name = userName, phone_number = phoneNumber, contact_message = contactMessage, email = email)
                if (orderedMenuItems is not None and len(orderedMenuItems) > 0):
                    background_tasks.add_task(create_order, uid=phoneNumber, user_name = userName, phone_number = phoneNumber, delivery_message = deliveryMessage, email = email, ordered_menu_items=orderedMenuItems, time_now = time_now)
                    new_user['currentOrderId'] = str(timestamp)
                return new_user
    except Exception as e:
        tb_info = traceback.format_tb(e.__traceback__)
        error_type = type(e).__name__
        error_msg = str(e)
        tb_str = ''.join(tb_info)
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))

        # Store the error information in a dictionary
        data = {
            'stackTrace': traceback_str,
            'message': str(e),
            'level': 'Critical'.upper(),
            'loggerName': 'pythonSource',
            'object': {
            'error_type': error_type,
            'error_msg': error_msg,
            'tb_info': tb_info,
            'tb_str': tb_str
        }}
        firestoreDB.collection('logs').document(str(get_cameroon_time_now())).set(data)


        raise HTTPException(status_code = 422, detail={"status": "failed", "reason":f"Exeption({e}) occurred when creating user for email = '{email}' phone number = '{phoneNumber}' EMAIL_PASSWORD = 'EMAIL_PASSWORD_HIDDEN', EMAIL_DOMAIN = '{EMAIL_DOMAIN}'"})

@app.get("/delete_inactive_anonymous_users/{requested_by}")
def delete_inactive_anonymous_users(
    requested_by: str = Path(..., min_length=5, max_length=40)):
    if requested_by not in [val for val in (os.environ.get('WHO_CAN_DELETE_ANON_USERS') or '').split() if val != '']:
        return {'message': f"Sorry, '{requested_by}' is not allowed to perform this action"}
    # Calculate the timestamp 1 day ago from the current time
    one_day_ago = datetime.now() - timedelta(days=1)

    # Get all anonymous users from Firebase Auth
    number_of_users = 1001
    user_list = []
    while number_of_users>= 1000:
        number_of_users = 0
        all_users = auth.list_users(max_results=1000)

        # Loop through each user and check their last login timestamp
        for user in all_users.iterate_all():
            user_id = user.uid
            number_of_users += 1
            last_login = user.user_metadata.last_sign_in_timestamp
            # If the user is an anonymous user and their last login is more than 1 day ago
            if len(user.provider_data) == 0 and last_login is not None and last_login < one_day_ago.timestamp()*1000:
                user_list.append(get_formatted_user_map(user))
                # Delete the user from Firebase Auth
                auth.delete_user(user_id)
        sleep(3)
    return {"deletedUsers": user_list}

@app.post("/link_user_with_email_and_password")
async def link_user_with_email_and_password(
                                    *,
                                    password: str = Form(..., min_length = 6),
                                    email: EmailStr = Form(...),):
    try:
        firestore_user = get_user_by_email(email)
        user = update_user(uid = firestore_user.uid, password=password, email=email)
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'email_verified': user.email_verified,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'disabled': user.disabled,
            'provider_id': user.provider_id,
        }
        return user_data
    except Exception as e:
        return {'message': str(e)}

@app.post("/link_user_with_facebook")
def link_user_with_facebook(
                                    *,
                                    email: EmailStr = Form(...),
                                    provider_id: str = Form('facebook.com'),
                                    token: str = Form(None),
                                    fb_uid: str = Form(...),
                                    display_name = Form(...),
                                    photo_url: str = Form(None)):


    # try:
    #facebook_credential = auth.FacebookAuthProvider.credential(accessToken)
    user = get_user_by_email(email)
    dic = {'rawId': '3207033952883339',
'displayName': 'Samuel M Nde',
'email': 'ndesamuelmbah@gmail.com',
'photoUrl':'https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=3207033952883339&height=800&ext=1682370327&hash=AeSxIfVqI9eneFCw14k',
'providerId':'facebook.com'}
    new_user_provider = ProviderUserInfo(dic)
    print(new_user_provider.uid)
    print('Trying to set provider data')
    user.provider_data.append(new_user_provider)
    # user_provider = user.provider_data
    # user_provider.append(new_user_provider)
    print('Reached here')
    auth.update_user(user)
    print('User updated')
    #user.provider_data = user_provider
    print('Has Set')

    # # Update the user record in Firebase Authentication
    # auth.update_user(user)
    # user.provider_data.append(new_user_info)

    # # Update the user record in Firebase Authentication
    # auth.update_user(user)
    # #user.link_with_credentials(facebook_credential)
    user_data = {
        'uid': user.uid,
        'email': user.email,
        'email_verified': user.email_verified,
        'display_name': user.display_name,
        'photo_url': user.photo_url,
        'disabled': user.disabled,
        'wasUpdated': True
    }
    return user_data
    # except Exception as e:
    #     print(e)
    #     return {'message': str(e)}
