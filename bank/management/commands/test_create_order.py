from django.core.management.base import BaseCommand
import requests


class Command(BaseCommand):
    help = 'Test'

    def handle(self, *args, **kwargs):
       url = 'https://p2p.jzc899.com/be_en/ashx/control.ashx'
       headers = {
           'Cookie':'ASP.NET_SessionId=wrcv4xdc1uhpjm1lvhyw5fmz; cf_clearance=tOj4ybSlDyTdYrQed1U9289CWBgHUizgfc3UPHiybmg-1718865515-1.0.1.1-vIcefcRai1OePod6Kt3.Pj7OLR_v5oc8IsJdgakeT9.dmvzP1.svYa3Q09oR5wznyfd8.qcvDySrkdXzAHs0Yg'
       }
       data = {
           'todo':'queryaccount'
       }
       response = requests.post(url=url, headers=headers, data=data)
       print(response.json())
       print("=== query service")
       data = {
           'todo':'queryservice',
           'ccode':'CID163',
           'status':1
       }
       response = requests.post(url=url, headers=headers, data=data)
       print(response.json())
       data = {
           'todo':'querybank',
           'ccode':'CID163',
           'scode':'CID16301',
           'status':0,
           'pageSize':1000,
           'hidden':0
       }
       response = requests.post(url=url, headers=headers, data=data)
       print(response.json())
       data = {
           'todo':'addbankorder',
           'bkid':'8684',
           'money':'50000.00',
           'postscript':'ZB3B4',
           'payname':'nam',
           'payacctno':'3783',
           'txid':''
       }
       response = requests.post(url=url, headers=headers, data=data)
       print('===', response.json())