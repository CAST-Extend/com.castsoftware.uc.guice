"""
Created on 2022-11-22

@author: KFU
"""
import cast_upgrade_1_6_13  # @UnusedImport
import cast.analysers.jee
from cast.analysers import log, CustomObject, Type
from cast.application import open_source_file
import re
import datetime


class GuiceAnalyzerLevel(cast.analysers.jee.Extension):

    def __init__(self):

        super(self).__init__()
        # Declaring a temporary file to exchange data between the analyzer level and the application level
        self.exchange_file = None

    def start_analysis(self, options):
        """
        @type options: cast.analysers.JEEExecutionUnit
        """
        log.info('Starting JEE Analysis for Google Guice Framework...')

        # Creating the temporary file to exchange data between the analyzer level and the application level
        self.exchange_file = self.get_intermediate_file('com.castsoftware.uc.guice.txt')
        log.info('Created file com.castsoftware.uc.guice.txt to store intermediary findings')

        # Adding a classpath for Guice
        options.add_classpath('lib-guice')
        log.info('Added Guice JARs to the classpath')

    def end_analysis(self):
        log.info('Ending JEE Analysis for Google Guice Framework')

    def start_member(self, member):
        """
        @type member: cast.analysers.Member
        """

        # Store all annotations
        member_annotations = member.get_annotations()

        # Iterate over the annotations to check whether this member is annotated for Guice
        for annotation in member_annotations:

            # If member is annotated with com.google.inject.Provides, store all other annotations into exchange_file
            if annotation[0].get_fullname() == 'com.google.inject.Provides':
                # Format used: BINDING;object_full_name;annotation;annotation;...
                # e.g. BINDING;com.example.App.MessageModule.provideMessage;com.example.App.Message;com.example.App.Printer
                data_to_store = 'BINDING;' + member.get_fullname() + ';' + ';'.join(
                    x[0].get_fullname()
                    for x in member_annotations
                    if x[0].get_fullname() != 'com.google.inject.Provides')

                self.exchange_file.write(data_to_store + '\n')
                log.info('Storing Guice Binding found through @Provides: ' + data_to_store)

            # If member is annotated with javax.inject.Inject, store annotations of parameters into exchange_file
            if annotation[0].get_fullname() == 'javax.inject.Inject':
                # Format used: INJECTION;object_full_name;annotation;annotation;...
                # e.g. INJECTION;com.example.App.App;Message;Count
                data_to_store = 'INJECTION;' + member.get_fullname() + ';' + ';'.join(
                    self._extract_parameters_annotations(member))

                self.exchange_file.write(data_to_store + '\n')
                log.info('Storing Guice injection found through @Inject: ' + data_to_store)

    def _extract_parameters_annotations(self, member):
        """
        @type member: cast.analysers.Member
        """

        signature = self._extract_signature(member)
        regex = re.compile(r'@([a-zA-Z0-9]+)')
        prefix = '.'.join(member.get_fullname().split('.')[:-1])

        return [prefix + '.' + x for x in regex.findall(signature)]

    def _extract_signature(self, member):
        """
        @type member: cast.analysers.Member
        """

        signature = ''
        bookmark = member.get_position()
        with open_source_file(member.get_position().get_file().get_path()) as file:
            line_count = 0
            for line in file:
                line_count += 1
                if line_count < bookmark.get_begin_line() or line_count > bookmark.get_end_line():
                    continue
                signature += line.rstrip()

        regex = re.compile(r'@Inject([a-zA-Z\(\), @_\/]+){')

        return regex.search(signature).group(1).strip()
