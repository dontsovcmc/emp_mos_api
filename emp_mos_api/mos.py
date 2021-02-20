# -*- coding: utf-8 -*-

from __future__ import print_function
import six
import time
from datetime import datetime, tzinfo
import requests
from copy import deepcopy

API_V1_0 = 'https://emp.mos.ru/v1.0'
API_V1_1 = 'https://emp.mos.ru/v1.1'


class AuthException(Exception):
    pass


class EmpServerException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        if six.PY2:
            super(Exception, self).__init__('{0} (code:{1})'.format(self.message.encode('utf-8'), self.code))
        else:
            super().__init__('{0} (code:{1})'.format(self.message, self.code))


class EmpCounterNotVerifiedException(EmpServerException):
    """
    'errorCode' 'errorMessage'
    3454: 'Не удалось передать показания за сентябрь по счётчикам <серийный номер>: "Невозможно внести показание, поскольку не введены показания за три и более месяца, предшествующих текущему. Для возобновления
           удалённой передачи показаний Вам следует обратиться в Центр госуслуг/ГКУ ИС района.
    """
    pass


class EmpAlreadySendException(EmpServerException):
    """Не удалось передать показания за X по счётчикам 12345678:
    "Вы не можете изменить показания, переданные через портал mos.ru или введенные сотрудниками" \
    " Центров госуслуг/ГКУ ИС." 12345678: "Редактируемое показание принято к расчёту." '
    """
    pass


class EmpHugeValueException(EmpServerException):
    """
    Не удалось передать показания за февраль по счётчикам 123456:
    "Не допускается внесение данных, в несколько раз превышающих нормативы водопотребления,
    установленные Правительством Москвы."  (code:3454)
    """
    pass

class EmpValueLessException(EmpServerException):
    """
    Не удалось передать показания за февраль по счётчикам 123456:
    "Вносимое показание меньше предыдущего. Проверьте корректность вносимого показания.
    В случае, если передаваемые данные корректны, Вам следует обратиться в
    Центр госуслуг/ГКУ ИС района для уточнения причин ошибки."  (code:3454)
    """
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
        self.user_agent = kwargs.get('user_agent', 'okhttp/3.8.1')
        self.dev_app_version = kwargs.get('dev_app_version')
        self.dev_user_agent = kwargs.get('dev_user_agent')

        self.post_request_data = {
            'info': {
                'guid': self.guid,
                'user_agent': self.dev_user_agent,
                'app_version': self.dev_app_version
            },
            'auth': {
                'session_id': self.session_id
            }
        }


        # 3.8.1.216(108)
        #self.dev_mobile = kwargs.get('dev_mobile')
        #self.info_field = {
        #    'app_version': self.dev_app_version,
        #    'guid': self.guid,
        #    'mobile': self.dev_mobile,
        #    'session_id': None,
        #    'user_agent': self.dev_user_agent
        #}

        self.headers = {
            'Cache-Control': 'no-cache',
            'Host': 'emp.mos.ru',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': self.user_agent
        }

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
        # print('Exec time:', answer['execTime'])

        code = answer['errorCode']
        msg = answer['errorMessage'] if 'errorMessage' in answer and answer['errorMessage'] else ''

        if code == 401:
            raise AuthException('Ошибка авторизации')

        if code == 3454:
            if u'показание принято к расчёту' in msg:
                raise EmpAlreadySendException(msg, code)
            elif u'Не допускается внесение данных, в несколько раз превышающих нормативы водопотребления' in msg:
                raise EmpHugeValueException(msg, code)
            elif u'Вносимое показание меньше предыдущего' in msg:
                raise EmpValueLessException(msg, code)
            elif u'Истёк срок поверки прибора учёта' in msg:
                raise EmpCounterNotVerifiedException(msg, code)

        if code != 0:
            raise EmpServerException(msg, code)

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
                'app_version': self.dev_app_version,
                #'mobile': self.dev_mobile  # 3.8.1.216(108)
            },
            'auth': {
                'login': telephone,
                'password': pwd,
                'guid': self.guid
            }
        }

        ret = self.session.post(API_V1_0 + '/auth/virtualLogin',
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
        self.post_request_data['auth']['session_id'] = self.session_id
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

        ret = self.session.get(API_V1_0 + '/profile/get',
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

        ret = self.session.get(API_V1_0 + '/flat/get',
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

    def address_search(self, pattern, limit=100):
        """
        :param pattern: строка шаблон для поиска
        :param limit: сколько ответов выводить
        :return:
        {
            "address": "",
            "description": "",
            "district": "",
            "fullMatch": False,
            "unad": 1,
            "unum": 123456
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({'Content-Type': 'application/json; charset=UTF-8'})

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'limit': limit,
            'pattern': pattern,
        })

        ret = self.session.post(API_V1_1 + '/flat/addressSearch',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def flat_delete(self, flat_id):
        """
        Удалить квартиру
        :param flat_id: unicode string from flat_response
            response[0]['flat_id']
        :return: Null
        """

        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WIDGETS,EPD,ELECTRO_COUNTERS,WATER_COUNTERS,APARTMENT, EPD_WIDGET,ACCRUALS_WIDGET',
                'Content-Type': 'application/json; charset=UTF-8' })

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id
        })

        ret = self.session.post(API_V1_0 + '/flat/delete',
                                params={'token': self.token},
                                headers=wheaders,
                                verify=self.verify,
                                timeout=self.timeout,
                                json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def flat_add(self, name, unom, unad, address, flat_number, paycode):
        """
        Добавление квартиры. Перед добавлением надо узнать unom
        :param name: имя квартиры. любое
        :param unom: INT из запроса addressSearch
        :param unad: INT из запроса addressSearch
        :param address: Любой
        :param flat_number: Номер квартиры. Любой. Но для отправки показаний нужен точный.
        :param paycode: Код плательщика
        :param electro_account: Номер счета Мосэнергосбыта
        :param electro_device: Серийный номер счетчика. Если заполнен, должен и номер Мосэнергосбыта быть заполнен.
        :return:

        {
            "flat_id":"23611975",
            "name":"",
            "address":"",
            "flat_number":"111",
            "unom":"3802879",
            "unad":"1",
            "paycode":"1234567890",
            "electro_account":"",
            "electro_device":"",
            "intercom":"",
            "floor":"",
            "entrance_number":"",
            "alias":"",
            "epd":"1234567890",
            "flat":"111",
            "building":"",
            "street": равно address
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WIDGETS,EPD,ELECTRO_COUNTERS,WATER_COUNTERS,APARTMENT, EPD_WIDGET,ACCRUALS_WIDGET',
                'Content-Type': 'application/json; charset=UTF-8'
        })

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'a': 0,
            'address': address,
            'can_update': False,
            'flat_number': flat_number,
            'name': name,
            'paycode': paycode,
            'unad': unad,
            'unom': unom
        })

        ret = self.session.post(API_V1_0 + '/flat/add',
                                params={'token': self.token},
                                headers=wheaders,
                                verify=self.verify,
                                timeout=self.timeout,
                                json=wcrequest)

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

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'is_widget': False
        })

        ret = self.session.post(API_V1_0 + '/watercounters/get',
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

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'counters_data': counters_data
        })

        ret = self.session.post(API_V1_0 + '/watercounters/addValues',
                                                     params={'token': self.token},
                                                     headers=wheaders,
                                                     verify=self.verify,
                                                     timeout=self.timeout,
                                                     json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def get_electrocounters(self, flat_id):
        """
        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :return:
        {
            "address": "город ...",
            "electro_account": "851xxxx475",
            "electro_device": "04xxx17",
            "balance": 0,
            "is_debt": false,
            "description": "Внимание! Передача показаний возможна с 15 по 26 число месяца. При вводе текущих показаний обращайте внимание на значность счетчиков. В случае если показания введены с неверной значностью (большей, чем значность счетчика), они не будут загружены.",
            "sh_znk": 5,
            "zones": [{
                "name": "T1",
                "value": "6887"
            }],
            "intervals": [{
                "name": "T1",
                "value": "00:00-23:59"
            }]
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'ELECTRO_COUNTERS',
                'X-Cache-ov-mode': 'DEFAULT',
                'Content-Type': 'application/json; charset=UTF-8' })

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'is_widget': False,
        })

        ret = self.session.post(API_V1_0 + '/electrocounters/get',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def send_electrocounters(self, flat_id, counters_data):
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
                'X-Clears-tags': 'ELECTRO_COUNTERS',
                'Content-Type': 'application/json; charset=UTF-8'
            })

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'counters_data': counters_data
        })

        ret = self.session.post(API_V1_0 + '/electrocounters/addValues',
                                                     params={'token': self.token},
                                                     headers=wheaders,
                                                     verify=self.verify,
                                                     timeout=self.timeout,
                                                     json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def get_epd(self, flat_id, period, is_debt=True):
        """
        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :param period: unicode string represents date in 27.09.2018 format
        :param is_debt: True/False
        :return:
        {
            "is_debt": true,
            "is_paid": true,
            "amount": 2982.77,
            "service_code": "emp.zkh",
            "insurance": 61.93,
            "ammount_insurance": 3044.7
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'EPD',
                'X-Cache-ov-mode': 'DEFAULT',
                'Content-Type': 'application/json; charset=UTF-8' })

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'period': period,
            'is_debt': is_debt,
        })

        ret = self.session.post(API_V1_1 + '/epd/get',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def get_eepd(self, flat_id, period, epd_type='current', rid=None):
        """
        Запросить электронный ЕПД (pdf). Первый запрос возвращает rid и документ начинает готовиться.
        Последующие запросы будут либо пустые, либо содержать ссылку на PDF + расшифровку полей.

        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :param period: unicode string represents date in 27.09.2018 format
        :param epd_type: current
        :param rid: Если None, то это первый запрос. В ответе будет rid, который нужно добавить в последующие запросы,
            пока документ готовится.
        :return:
        Первый ответ и последующие , пока не готов документ
        {
            "rid": GUID,
        }

        {
            "pdf": Ссылка на pdf,
            "title": "Платежный документ",
            "sections": [
                {
                    "title": "Начисления",
                    "elements": {
                        "address": "xxxx",
                        "epd": 123455,
                        "hint": "text",
                        "payment_elements": [
                            ],
                        "period": "DD-месяц-YYYY",
                        "total_elements": [
                        ]
                    }
                },
                {
                    "title": "Информация",
                    "elements": [
                        {
                            "title": "text",
                            "body": "text"
                        },
                        {
                        }
                    ]
                }
            ]
        }

        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'Content-Type': 'application/json; charset=UTF-8'})

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'flat_id': flat_id,
            'period': period,
            'type': epd_type,
        })

        if rid:
            wcrequest.update({'rid': rid})

        ret = self.session.post(API_V1_0 + '/eepd/get',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def get_eepd_wait_result(self, flat_id, period, timeout=10.0):
        """
        Запросить электронный ЕПД (pdf) и дождаться результата

        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :param period: unicode string represents date in 27.09.2018 format
        :param timeout: сколько ждем в секундах результата
        """
        start = time.time()

        rid = None
        result = None
        while not result and time.time() - start < timeout:
            time.sleep(2.0)

            ret = self.get_eepd(flat_id, period, 'current', rid)
            if 'rid' in ret:
                rid = ret['rid']

            if 'pdf' in ret:
                result = deepcopy(ret)

        return result

    def get_car_fines(self, sts_number):
        """
        :param sts_number: unicode string contains car sts_numer
        :return:
        {
            "paid": [{
                "seriesAndNumber": "xxxxx",
                "date": "2018-08-30+03:00",
                "offence_place": "МОСКВА Г.   МКАД,xxxx, ВНЕШНЯЯ СТОРОНА",
                "offenceType": "12.9ч.2 - Превышение установленной скорости движения транспортного средства на величину от 20 до 40 километров в час  ",
                "cost": "500",
                "is_discount": false,
                "drive_license": null,
                "sts_number": "xxxxxxx",
                "executionState": "Исполнено",
                "is_fssp": false
            }],
            "unpaid": []
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'FORCE_NETWORK',
                'X-Cache-ov-mode': 'DEFAULT',
                'Content-Type': 'application/json; charset=UTF-8'})

        wcrequest = deepcopy(self.post_request_data)
        wcrequest.update({
            'sts_number': sts_number
        })

        ret = self.session.post(API_V1_0 + '/offence/getOffence',
                                 params={'token': self.token},
                                 headers=wheaders,
                                 verify=self.verify,
                                 timeout=self.timeout,
                                 json=wcrequest)

        response = ret.json()
        self.raise_for_status(response)
        return response['result']

    def logout(self, timeout=None):
        """
        Почему то очень долго выполняется (5 сек)
        """
        if self.session_id:
            logout_data = deepcopy(self.post_request_data)

            ret = self.session.post(API_V1_0 + '/auth/logout',
                         params={'token': self.token},
                         headers=self.headers,
                         timeout=timeout or self.timeout,
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
        if client_id and client_id not in self._clients:
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

    # Квартиры
    def get_flats(self):
        return self.client().get_flats()

    def flat_delete(self, *args):
        return self.client().flat_delete(*args)

    def flat_add(self, *args):
        return self.client().flat_add(*args)

    def address_search(self, *args):
        return self.client().address_search(*args)

    # Счетчики воды
    def get_watercounters(self, *args):
        return self.client().get_watercounters(*args)

    def send_watercounters(self, *args):
        return self.client().send_watercounters(*args)

    # Счетчики электроэнергии
    def get_electrocounters(self, *args):
        return self.client().get_electrocounters(*args)

    def send_electrocounters(self, *args):
        return self.client().send_electrocounters(*args)

    # Единый платежный документ
    def get_epd(self, *args):
        return self.client().get_epd(*args)

    # Сформировать pdf Единый платежный документ
    def get_eepd_wait_result(self, *args):
        return self.client().get_eepd_wait_result(*args)

    # Штрафы
    def get_car_fines(self, *args):
        return self.client().get_car_fines(*args)


class Water:
    COLD = 1
    HOT = 2

    @staticmethod
    def water_abbr(water):
        if water == Water.COLD:
            return u'ХВС'
        elif water == Water.HOT:
            return u'ГВС'

    @staticmethod
    def name(water):
        if water == Water.COLD:
            return u'холодная вода'
        elif water == Water.HOT:
            return u'горячая вода'


class Watercounter:
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
        None - когда показания не сданы более 3-х месяцев
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
        checkup = counter['checkup'].split('+')[0]  # python 3.6 support https://stackoverflow.com/questions/53291250/python-3-6-datetime-strptime-returns-error-while-python-3-7-works-well
                                                    # ValueError: time data '2023-08-08+03:00' does not match format '%Y-%m-%d%z'↵"
        d = datetime.strptime(checkup, '%Y-%m-%d')  #'checkup': '2023-09-25+03:00'
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
