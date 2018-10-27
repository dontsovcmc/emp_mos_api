# -*- coding: utf-8 -*-
from __future__ import print_function
import requests
from datetime import datetime, tzinfo
from copy import deepcopy


class AuthException(Exception):
    pass

class EmpServerException(Exception):
    pass


class Client(object):
    """
    Клиента
    """
    def __init__(self, **kwargs):
        self.token = kwargs.get('token')
        self.guid = kwargs.get('guid')

        #requests
        self.verify = kwargs.get('verify', True)
        self.timeout = kwargs.get('timeout', 3.0)

        self.session_id = None  # emp mos ru
        self.user_agent = kwargs.get('user_agent')
        self.dev_app_version = kwargs.get('dev_app_version')
        self.dev_user_agent = kwargs.get('dev_user_agent')
        self.headers = {'Cache-Control': 'no-cache',
                   'Host': 'emp.mos.ru',
                   'Connection': 'Keep-Alive',
                   'Accept-Encoding': 'gzip',
                   'User-Agent': self.user_agent}
        self.pheaders = deepcopy(self.headers)
        self.pheaders.update({
            'X-Cache-ov': '15552000',
            'X-Cache-ov-mode': 'FORCE_NETWORK'
        })
        self.session = requests.Session()

    def raise_for_status(self, answer):
        """
        :param answer: JSON
        {
            u'errorCode': 0, # 0-OK,
                               401-Auth error
            u'execTime': 0.138262,
            u'errorMessage': u'', # error message
            u'session_id': u'6c3333333c33333e44e21e7d43c46e03',
            u'result': None or JSON
        }
        :return:
        """
        print('Exec time:', answer['execTime'])
        if answer['errorCode'] == 401:
            raise AuthException()

        if answer['errorCode'] != 0:
            if answer['errorMessage']:
                raise EmpServerException(u'{0} (code:{1})'.format(answer['errorMessage'], answer['errorCode']))
            raise EmpServerException(u'code:{0}'.format(answer['errorCode']))

    def is_active(self):
        """
        :return: True если уже залогинился
        """
        return self.session_id is not None

    def login(self, telephone, pwd):
        """
        :param telephone: Телефон. Вид: 7xxxxxxxxxx
        :param pwd: Пароль из приложения Госуслуги Москвы
        :return: JSON
        {
            u'is_filled': True,
            u'surname': u'x',
            u'name': u'x',
            u'session_id': u'6c3333333c33333e44e21e7d43c46e03'},
            u'request_id': u'UN=PRO-12345678-1234-1234-1234-123456789123'
        }
        """
        login_data = {
            'device_info': {
                'guid': self.guid,
                'user_agent': self.dev_user_agent,
                'app_version': self.dev_app_version
            },
            'auth': {
                'login': telephone,
                'password': pwd,
                'guid': self.guid
            }
        }

        ret = self.session.post('https://emp.mos.ru/v1.0/auth/virtualLogin',
                     params={'token': self.token},
                     headers={'Content-Type': 'application/json; charset=UTF-8',
                              'Connection': 'Keep-Alive',
                              'Accept-Encoding': 'gzip',
                              'User-Agent': self.user_agent,
                              'cache-control': 'no-cache',
                              'Host': 'emp.mos.ru',
                              'Accept': '*/*'},
                     verify=self.verify,
                     timeout=self.timeout,
                     json=login_data)

        response = ret.json()
        self.raise_for_status(response)
        self.session_id = response['session_id']
        return response['result']

    def get_profile(self):
        """
        :return: JSON
        {
            u'drive_license': None,
            u'firstname': u'x',
            u'middlename': u'x',
            u'lastname': u'x',
            u'birthdate': u'dd.mm.YYYY',
            u'msisdn': u'71234567890',  # your telephone
            u'email_confirmed': True,
            u'email': u'x@x.ru'
        }
        """
        assert self.session_id

        ret = self.session.get('https://emp.mos.ru/v1.0/profile/get',
                                params={'token': self.token,
                                        'info[guid]': self.guid,
                                        'auth[session_id]': self.session_id
                                        },
                                headers=self.pheaders,
                                verify=self.verify,
                                timeout=self.timeout)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']['profile']

    def get_flats(self):
        """
        :return: JSON array
        [{
            u'name': u'x',
            u'paycode': u'1234567890',
            u'flat_id': u'1234567',
            u'electro_account': None,
            u'flat_number': u'0',
            u'unad': u'0',
            u'address': u'x',
            u'electro_device': None,
            u'unom': u'1234567' # Идентификатор дома
        },{...}
        ]
        """
        assert self.session_id

        ret = self.session.get('https://emp.mos.ru/v1.0/flat/get',
                                params={'token': self.token,
                                        'info[guid]': self.guid,
                                        'auth[session_id]': self.session_id
                                        },
                                headers=self.pheaders,
                                verify=self.verify,
                                timeout = self.timeout)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def get_watercounters(self, flat_id):
        """
        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :return:
        {
            u'stat_title': u'x',
                u'archive': [
                    {
                        u'cold_indication': 1.55,
                        u'hot_indication': 1.2,
                        u'period': u'2017-08-31+03:00'
                    }, {
                        u'cold_indication': 1.3,
                        u'hot_indication': 0.39999999999998,
                        u'period': u'2017-09-30+03:00'
                    }, {
                        +10 эл-тов. Всего 12.
                    }],
                u'counters': [
                    {
                        u'checkup': u'2021-08-08+03:00', # дата поверки
                        u'counterId': 123456, # id счетчика в emp.mos.ru
                        u'num': u'123456',  # серийный номер счетчика
                        u'type': 1,  # ХВС
                        u'indications': [
                            {
                                u'indication': u'200.24',
                                u'period': u'2018-07-31+03:00'
                            }, {
                                u'indication': u'200.6',
                                u'period': u'2018-06-30+03:00'
                            }, {
                                u'indication': u'200.5',
                                u'period': u'2018-05-31+03:00'
                            }, {
                                u'indication': u'200.5',
                                u'period': u'2018-04-30+03:00'
                            }]
                    },
                    {..}
                ]
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WATER_COUNTERS',
                'X-Cache-ov-mode': 'DEFAULT',
                'Content-Type': 'application/json; charset=UTF-8' })

        wcrequest = {
            'flat_id': flat_id,
            'is_widget': False,
            'info': {
                'guid': self.guid
            },
            'auth': {
                'session_id': self.session_id
            }
        }

        ret = self.session.post('https://emp.mos.ru/v1.0/watercounters/get',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def send_watercounters(self, flat_id, counters_data):
        """
        :param flat_id: flat_response['flat_id']
        :param counters_data: array of
            [{
                'counter_id': u'123456', # ['counters'][0]['counterId']
                'period': datetime.now().strftime("%Y-%m-%d"),
                'indication': 'xxx,xx'
            }, {
                ...
            }]
        :return:
        """
        assert self.session_id

        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WATER_COUNTERS',
                'Content-Type': 'application/json; charset=UTF-8'
            })

        wcrequest = {'flat_id': flat_id,
                     'counters_data': counters_data,
                     'info': {
                        'guid': self.guid
                     },
                     'auth': {
                        'session_id': self.session_id
                     }}

        ret = self.session.post('https://emp.mos.ru/v1.0/watercounters/addValues',
                                                     params={'token': self.token},
                                                     headers=self.wheaders,
                                                     verify=self.verify,
                                                     timeout=self.timeout,
                                                     json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def logout(self):
        """
        Почему то очень долго выполняется (5 сек)
        """
        if self.session_id:
            logout_data = {
                'info': {
                    'guid': self.guid
                },
                'auth': {
                    'session_id': self.session_id
                }
            }
            ret = self.session.post('https://emp.mos.ru/v1.0/auth/logout',
                         params={'token': self.token},
                         headers=self.headers,
                         timeout=self.timeout,
                         json=logout_data)

            response = ret.json()
            self.raise_for_status(response)
            self.session_id = None
            return response['result']


class MosAPI(object):
    """
    kwargs:

    token:           уникальный ключ приложения
    guid:            некий уникальный ключ
    https_verify:    ключ verify в GET, POST запросах, по умолчанию 'False'
    timeout:         ключ timeout в GET, POST запросах
    user_agent:      версия веб клиента
    dev_user_agent: 'Android' для ОС Android
    dev_app_version: версия ОС
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._clients = {'default': Client(**kwargs)}

    def client(self, client_id='default', **kwargs):
        if client_id and \
            client_id not in self._clients:
            k = self.kwargs
            k.update(kwargs)
            self._clients[client_id] = Client(**k)
        return self._clients[client_id]

    # if only one client
    def is_active(self):
        return self.client().is_active()
    def login(self, *args):
        return self.client().login(*args)
    def logout(self, *args):
        return self.client().logout(*args)

    def get_profile(self):
        return self.client().get_profile()
    def get_flats(self):
        return self.client().get_flats()
    def get_watercounters(self, *args):
        return self.client().get_watercounters(*args)
    def send_watercounters(self, *args):
        return self.client().send_watercounters(*args)


class Water():
    COLD = 1
    HOT = 2

    @staticmethod
    def water_abbr(water):
        if water == Water.COLD: return u'ХВС'
        elif water == Water.HOT: return u'ГВС'

    @staticmethod
    def name(water):
        if water == Water.COLD: return u'холодная вода'
        elif water == Water.HOT: return u'горячая вода'


class Watercounter():
    """
    [{ 'counterId': 1437373, # внутреннее id счетчика
       'type': 1,            # тип воды
       'num': '417944',      # серийный номер счетчика
       'checkup': '2023-09-25+03:00',  # дата следующей поверки
       'indications':
           [{'period': '2018-08-31+03:00', 'indication': '21.38'},
           {'period': '2018-07-31+03:00', 'indication': '20.7'},
           {'period': '2018-06-30+03:00', 'indication': '19'}]
           },
           {...}
    ]

    list(filter(lambda x: x['num'] == num, response['counters']))
    list(filter(lambda x: x['counterId'] == id, response['counters']))
    list(filter(lambda x: x['type'] == water_type_id, response['counters']))
    """

    @staticmethod
    def last_value(counter):
        """
        alphabetical sort data =)
        :param counter: counter JSON
        :return: float or None
        """
        indications = counter['indications']
        indications.sort(key=lambda x: x['period'])
        if indications:
            return float(indications[-1]['indication'])

    @staticmethod
    def water_title(counter):
        return Watercounter.humanreadable_name(counter['type'])

    @staticmethod
    def checkup(counter):
        """
        https://docs.python.org/3/library/datetime.html#datetime.timezone
        Если нужно UTC d.replace(tzinfo=None)

        :param counter: counter JSON
        :return: datetime с временной зоной
        """
        checkup = counter['checkup']
        d = datetime.strptime(checkup, '%Y-%m-%d%z')  #'checkup': '2023-09-25+03:00'
        return d

    @staticmethod
    def serialize_for_send(counter, value):
        """
        :param counterId: id счетчика. не номер из приложения!
        :param value: значение float
        :return: dict
        """
        return {
            'counter_id': int(counter['counterId']),
            'period': datetime.now().strftime("%Y-%m-%d"),
            'indication': '{:.2f}'.format(value).replace('.', ',')
        }
