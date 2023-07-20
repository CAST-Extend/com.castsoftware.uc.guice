"""
Created on 2022-11-22

@author: KFU
"""
import cast_upgrade_1_6_13  # @UnusedImport
from cast.application import ApplicationLevelExtension, create_link, Object
from cast.analysers import log
import logging


class GuiceApplicationLevel(ApplicationLevelExtension):

    def end_application(self, application):
        logging.warning('BLOOP')
        logging.info('Starting Application level Analysis for Google Guice Framework...')

        # Fetching temporary file with data generated at the analyzer level
        # Formats expected:
        # BINDING;object_full_name;annotation;annotation;...
        # INJECTION;object_full_name;annotation;annotation;...
        # e.g.
        # BINDING;com.example.App.MessageModule.provideMessage;com.example.App.Message;com.example.App.Printer
        # INJECTION;com.example.App.App;Message;Count
        exchange_file = self.get_intermediate_file('com.castsoftware.uc.guice.txt')
        injections, bindings = self._load_content_from_file(exchange_file)

        # logging.info('PLIF ' + str(injections))

        for method, src_annotations in injections.items():
            logging.info('Working on ' + method + ' annotated with ' + ', '.join(src_annotations))

            for src_annotation in src_annotations:
                for target_object_name, dest_annotations in bindings.items():
                    for dest_annotation in dest_annotations:
                        if dest_annotation == src_annotation:
                            logging.info('damm found ' + dest_annotation + ' same as ' + src_annotation)
                            logging.info('will create link from ' + method + ' to ' + target_object_name)

                            src = None
                            dest = None
                            for o in application.objects().has_type('Java').is_executable().has_type(
                                    ['JV_CTOR', 'JV_GENERIC_METHOD', 'JV_METHOD']):
                                #logging.warning('checking ' + o.get_fullname() + ' with types ' + str(o.get_type()))
                                if o.get_fullname() == method:
                                    src = o
                                if o.get_fullname() == target_object_name:
                                    dest = o

                            if src is not None and dest is not None:
                                logging.info('link created dude')
                                l = create_link('useLink', src, dest)
                                #l.add_bookmark(src.get_positions())

        logging.info('done ciao')

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
            log.warning(str(lines_not_imported)
                        + ' lines from the exchange file were not imported. They might be formatted incorrectly. Check the file at '
                        + exchange_file.filename())

        return injections, bindings
