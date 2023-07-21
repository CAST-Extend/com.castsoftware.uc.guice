"""
Created on 2022-11-22

@author: KFU
"""
import cast_upgrade_1_6_13  # @UnusedImport
from cast.application import ApplicationLevelExtension, create_link, Object
import logging


class GuiceApplicationLevel(ApplicationLevelExtension):

    def end_application(self, application):
        self._log('Starting Application level Analysis for Google Guice Framework...')

        # Fetching temporary file with data generated at the analyzer level
        # Formats expected:
        # BINDING;object_full_name;annotation;annotation;...
        # INJECTION;object_full_name;annotation;annotation;...
        # e.g.
        # BINDING;com.example.App.MessageModule.provideMessage;com.example.App.Message;com.example.App.Printer
        # INJECTION;com.example.App.App;Message;Count
        exchange_file = self.get_intermediate_file('com.castsoftware.uc.guice-temp-data.txt')
        injections, bindings = self._load_content_from_file(exchange_file)

        for method, src_annotations in injections.items():
            self._log('Working on ' + method + ' annotated with ' + ', '.join(src_annotations))

            for src_annotation in src_annotations:
                for target_object_name, dest_annotations in bindings.items():
                    for dest_annotation in dest_annotations:

                        match = False

                        # Strict match, e.g. xxx.yyy.zzz == xxx.yyy.zzz
                        if dest_annotation == src_annotation:
                            match = True
                            self._log('Found one strict match on ' + src_annotation
                                      + '. Creating link from '
                                      + method + ' to ' + target_object_name)

                        # Loose match, e.g. zzz == zzz
                        # dest_annotation can be modified without impact. But not src_annotation
                        dest_annotation = dest_annotation.split('.')[-1]
                        if not match and dest_annotation == src_annotation.split('.')[-1]:
                            match = True
                            self._log('Found one loose match on ' + dest_annotation
                                      + '. Creating link from '
                                      + method + ' to ' + target_object_name)

                        # Link creation
                        if match:
                            src = None
                            dest = None
                            for o in application.objects().has_type('Java').is_executable().has_type(
                                    ['JV_CTOR', 'JV_GENERIC_METHOD', 'JV_METHOD']):
                                if o.get_fullname() == method:
                                    src = o
                                if o.get_fullname() == target_object_name:
                                    dest = o

                            if src is not None and dest is not None:
                                l = create_link('useLink', src, dest)
                                self._log('Link created')
                                # TODO bookmark management? use the exact annotation bookmark for the link
                                # l.add_bookmark(src.get_positions())

        self._log('Done parsing the temporary data file created during the JEE analysis')

        # parcourt les injections
        # for each, chercher les mappings qui peuvent correspondre
        # si match, créer lien

        # correspondance stricte sur fullname, si pas de match, relaxer en supprimant des niveaux intermédiaires

    def _load_content_from_file(self, exchange_file):
        injections = {}
        bindings = {}
        count = 0
        for line in exchange_file:
            count += 1
            if line.find('INJECTION') == 0:
                injection = line.rstrip().split(';')
                injection.pop(0)
                method = injection.pop(0)
                injections[method] = injection
            if line.find('BINDING') == 0:
                target = line.rstrip().split(';')
                target.pop(0)
                method = target.pop(0)
                bindings[method] = target

        lines_not_imported = count - len(injections) - len(bindings)
        if lines_not_imported > 0:
            self._log(str(lines_not_imported)
                      + ' lines from the exchange file were not imported. They might be formatted incorrectly. Check the file at '
                      + exchange_file.filename(), 'warning')

        return injections, bindings

    def _log(self, msg, level='info'):
        msg = '[com.castsoftware.uc.guice] ' + msg
        if level == 'info':
            logging.info(msg)
        elif level == 'warning':
            logging.warning(msg)
        elif level == 'error':
            logging.error(msg)
