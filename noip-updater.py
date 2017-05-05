import os
import base64
import atexit
import getpass
import logging
import configparser

from http.client import HTTPConnection
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

logger = logging.basicConfig(filename='noip-updater.log', format='%(asctime)s %(levelname)s: %(message)s',
                             datefmt='%d-%m-%Y %H:%M:%S')


class Configuration:
    def __init__(self, configuration_directory):
        self.sectionName = 'DEFAULT'
        self.configuration = configparser.ConfigParser()
        self.configurationFile = os.path.join(configuration_directory, 'configuration.ini')
        # Writing default configuration file
        if not os.path.exists(self.configurationFile):
            self.configuration[self.sectionName] = {
                'no-ip-username': 'username',
                'no-ip-password': 'password',
                'no-ip-hostname': 'mytest.testdomain.com',
                'no-ip-update-interval-minutes': 5
            }
            self.save_configuration()
        else:
            self.read_configuration()

    def __contains__(self, index):
        return index in self.configuration[self.sectionName]

    def __getitem__(self, index):
        return self.configuration[self.sectionName][index]

    def __setitem__(self, index, value):
        self.configuration[self.sectionName][index] = value

    def save_configuration(self):
        with open(str(self.configurationFile), 'w') as fileWriter:
            self.configuration.write(fileWriter)
            print('Wrote default configuration file on ' + self.configurationFile)

    def read_configuration(self):
        self.configuration.read(self.configurationFile)


def task_listener(event):
    if event.exception:
        logging.error("Task didn't work as excepted: " + str(event.exception))
    else:
        logging.info('No-ip should be updated')


def noip_update(username, password, hostname):
    # http_connection = HTTPConnection(host='https://dynupdate.no-ip.com/nic/update', port=80, timeout=15)
    # request = http_connection.request(method='GET', url='https://dynupdate.no-ip.com/',
    #                                   body='nic/update?hostname=' + hostname,
    #                                   headers={'Host': 'dynupdate.no-ip.com',
    #                                            'Authorization': 'Basic base64-encoded-auth-string',
    #                                            'User-Agent': 'pythonprogram/0.1'
    #                                            })
    # http_connection.send(request)
    # response = http_connection.getresponse()
    # logging.debug('HttpResponse:' + str(response))
    # http_connection.close()
    return


class Updater:
    def __init__(self):
        print('Checking configuration directory')
        configuration_directory = os.path.join(os.path.expanduser('~'), '.noip-updater')
        if not os.path.exists(configuration_directory):
            os.mkdir(configuration_directory)
            print('Created configuration folder at ' + str(configuration_directory))

        print('Reading configuration')
        self.configuration = Configuration(configuration_directory)
        if self.configuration['no-ip-username'].lower() == 'username':
            self.configuration['no-ip-username'] = input("Enter the no-ip username: ")
            self.configuration['no-ip-password'] = getpass.getpass("Enter the password: ")
            self.configuration['no-ip-hostname'] = input("Enter the hostname (ex. mytest.testdomain.com): ")
            self.configuration['no-ip-update-interval-minutes'] = \
                input("Enter the interval to no-ip update in minutes: ")
            self.configuration.save_configuration()

        print('Starting scheduler')
        jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')}
        self.scheduler = BlockingScheduler(jobstores)
        if self.scheduler.get_job(job_id='no-ip-update-task') is None:
            logging.info("Registering job 'no-ip-update-task")
            self.scheduler.add_job(noip_update, 'interval', [
                self.configuration['no-ip-username'],
                self.configuration['no-ip-password'],
                self.configuration['no-ip-hostname']
            ], id='no-ip-update-task', max_instances=1, replace_existing=True,
                                   minutes=int(self.configuration['no-ip-update-interval-minutes']))
        self.scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        print('Registering quit task')
        atexit.register(self.exit_handler)
        logging.info('Starting scheduler')
        self.scheduler.start()

    def exit_handler(self):
        logging.info('Quitting scheduler')
        self.scheduler.shutdown()
        logging.shutdown()


def main():
    print("=== No-IP Updater - Rafael 'jabyftw' Sartori v0.1 ===")
    updater = Updater()


if __name__ == '__main__':
    main()
