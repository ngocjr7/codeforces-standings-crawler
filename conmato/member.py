from __future__ import absolute_import
from pyquery import PyQuery as pq
from .parameters import *
from .utils import *
import requests
import pandas as pd
import re, os
import datetime

def remove_participants(ss, member, groupID=GROUP_ID):
    url = MEMBERS_URL.format(groupID)
    payload = {
        '_tta': member['_tta'],
        'action': 'removeMember',
        'csrf_token': member['csrf_token'],
        'memberGroupRoleId': member['groupRoleId']
    }
    response = ss.post(url, data=payload)
    if response.status_code != 200:
        logger.warning('confirm_joining: an error occurred while confirming')

def remove_all_participants(ss, user_format=r'.*', groupID=GROUP_ID):
    members = get_all_members(ss, groupID)
    for member in members:
        if member['pending'] == True or member['role'] == 'manager':
            continue
        if re.search(user_format,member['username']):
            remove_participants(ss, member, groupID)
        se = random.uniform(float(TIMESLEEP)/2, TIMESLEEP)
        time.sleep(se)

def confirm_joining(ss, member, action, groupID=GROUP_ID):
    url = MEMBERS_URL.format(groupID)
    payload = {
        '_tta': member['_tta'],
        'action': 'confirmJoining',
        'confirmed': action,
        'csrf_token': member['csrf_token'],
        'groupRoleId': member['groupRoleId']
    }
    response = ss.post(url, data=payload)
    if response.status_code != 200:
        logger.warning('confirm_joining: an error occurred while confirming')


def confirm_all_participants(ss, action, user_format=USER_FORMAT, groupID=GROUP_ID):
    """
        if action == 'accept' -> accept all user that match user_format
        if action == 'reject' -> reject all user that not match user_format
    """
    members = get_pending_participants(ss, groupID)
    if action != 'accept' and action != 'reject':
        logger.warning('confirm_all_participants: cannot recognize action')
        return

    for member in members:
        if re.search(user_format,member['username']) and action == 'accept':
            confirm_joining(ss, member, action, groupID)
        elif not re.search(user_format,member['username']) and action == 'reject':
            confirm_joining(ss, member, action, groupID)
        se = random.uniform(float(TIMESLEEP)/2, TIMESLEEP)
        time.sleep(se)

def get_pending_participants(ss, groupID=GROUP_ID):
    url = MEMBERS_URL.format(groupID)
    response = ss.get(url)
    doc = pq(response.text)
    table = doc('table').not_('.rtable').not_('.table-form')

    members = []
    for tr in pq(table.children())[1:]:
        if pq(tr).children().eq(5).children().eq(0).is_('form'):
            member = {}
            member['username'] = pq(tr).children().eq(0)('a').eq(0).text()
            member['groupRoleId'] = pq(tr).children().eq(5).children().eq(0)('input').eq(2).attr('value')
            member['csrf_token'] = pq(tr).children().eq(5).children().eq(0)('input').eq(0).attr('value')
            member['_tta'] = 961
            members.append(member)

    return members

def get_all_members(ss, groupID=GROUP_ID):
    url = MEMBERS_URL.format(groupID)
    response = ss.get(url)
    doc = pq(response.text)
    table = doc('table').not_('.rtable').not_('.table-form')

    members = []
    for tr in pq(table.children())[1:]:
        member = {}
        member['username'] = pq(tr).children().eq(0)('a').eq(0).text()
        if member['username'] == '':
            continue
        
        member['csrf_token'] = pq(tr).children().eq(0)('form')('input').eq(0).attr('value')
        member['groupRoleId'] = pq(tr).children().eq(0)('form')('input').eq(2).attr('value')
        member['_tta'] = 961
        if pq(tr).children().eq(5).children().eq(0).is_('form'):
            member['pending'] = True
        else:
            member['pending'] = False

        if pq(tr).children().eq(1).text().lower() == 'creator':
            member['role'] = 'manager'
        else: 
            member['role'] = 'spectator'
        for option in pq(tr).children().eq(1)('select')('option'):
            if pq(option).attr['selected'] == 'selected':
                member['role'] = pq(option).val().lower()
    
        members.append(member)
    return members
        

def is_manager(groupID=GROUP_ID, username='', password=''):
    """
        check if user is manager of codeforces group
        Return:
            True, False
    """	
    if username == '' or password == '':
        logger.warning("isManager:Please provide username and password before using.")
        return False
    
    tmp_ss = requests.Session()
    url = MEMBERS_URL.format(groupID)
    response = tmp_ss.get(url)
    doc = pq(response.text)
    members = {}
    for e in doc('table').eq(1).children():
        username_tmp = pq(e)('td').eq(0).text()
        mtype_tmp = pq(e)('td').eq(1).text()
        members[username_tmp.lower()] = mtype_tmp.lower()

    payload = {
        "handleOrEmail": username,
        "password": password,
        "csrf_token": "",
        "bfaa": '1ef059a32710a29f84fbde5b5500d49c',
        "action": 'enter',
        "ftaa": 'uf8qxh8b5vphq6wna4',
        "_tta": 569
    }
    response = tmp_ss.get(LOGIN_URL)
    doc = pq(response.text)
    payload['csrf_token'] = doc('input').attr('value')

    response = tmp_ss.post(
        LOGIN_URL, 
        data = payload, 
        headers = dict(referer=LOGIN_URL)
    )

    doc = pq(response.text)
    username_again = doc('div').filter('.lang-chooser').children().eq(1).children().eq(0).text()
    if username_again == None or username.lower() != username_again.lower():
        logger.warning('isManager:Login failed, wrong username or password')
        return False 

    if username.lower() in members and members[username.lower()] == 'manager':
        return True
    logger.warning('isManager:Username isnot members or manager of codeforces group')
    return False