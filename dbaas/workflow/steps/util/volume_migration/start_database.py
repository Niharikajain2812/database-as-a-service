# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0022
from workflow.steps.util.restore_snapshot import use_database_initialization_script

LOG = logging.getLogger(__name__)


class StartDatabase(BaseStep):

    def __unicode__(self):
        return "Starting database..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            for host in workflow_dict['hosts']:
                cs_host_attr = CsHostAttr.objects.get(host=host)

                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=cs_host_attr.vm_user,
                                                  password=cs_host_attr.vm_password,
                                                  command='mount /data',
                                                  output=output)

                if return_code != 0:
                    raise Exception(str(output))

                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            databaseinfra = workflow_dict['databaseinfra']
            for host in workflow_dict['hosts']:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='stop')

                if return_code != 0:
                    LOG.info(str(output))

                cs_host_attr = CsHostAttr.objects.get(host=host)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=cs_host_attr.vm_user,
                                                  password=cs_host_attr.vm_password,
                                                  command='umount /data',
                                                  output=output)

                if return_code != 0:
                    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
