"""
Created on 2022-11-22

@author: KFU
"""
import cast_upgrade_1_6_13  # @UnusedImport
from cast import application
from cast.application import ApplicationLevelExtension, create_link, Object
import logging


class GuiceApplicationLevel(ApplicationLevelExtension):

    def end_application(self, application):
        self._log('Starting Application level Analysis for Google Guice Framework...')

        # Finding methods annotated with @Inject
        # i.e. javax.inject.Inject
        objects_using_guice = self._find_methods_using_an_annotation(application, ['javax.inject.Inject'])
        self._log('Working on ' + str(len(objects_using_guice)) + ' objects annotated with @Inject')

        # Listing all other annotations tied to the methods found
        objects_using_guice_with_their_annotations = self._find_annotations_for_these_methods(application,
                                                                                              objects_using_guice,
                                                                                              ['javax.inject.Inject'])

        # Finding @Provides methods that share the same annotations and creating the link
        # i.e. com.google.inject.Provides
        self._create_links(application, objects_using_guice_with_their_annotations)

    def _find_methods_using_an_annotation(self, application, annotations):
        """
        @type application: cast.application.Application
        """

        all_annotations = application.objects().has_type('CAST_Java_AnnotationType')
        annotation_objects_to_search = []
        for d in all_annotations:
            if d.get_fullname() in annotations:
                annotation_objects_to_search.append(d)

        all_methods = application.objects().has_type('Java').is_executable().has_type(
            ['JV_CTOR', 'JV_GENERIC_METHOD', 'JV_METHOD'])

        # Query selecting all links that start from methods and end in @Inject annotations
        links = application.links().has_caller(all_methods).has_callee(annotation_objects_to_search)
        objects_matching = []
        for l in links:
            self._log('Object found using @' + ', @'.join(annotations) + ': ' + l.get_caller().get_fullname())
            objects_matching.append(l.get_caller())

        return objects_matching

    # Returns a dict of object->[annotations]
    def _find_annotations_for_these_methods(self, application, methods_to_search_in, annotations_to_exclude=None):
        """
        @type application: cast.application.Application
        """

        # Query selecting all links that start from select methods and end in annotations
        all_annotations = application.objects().has_type('CAST_Java_AnnotationType')
        links = application.links().has_caller(methods_to_search_in).has_callee(all_annotations)
        total = str(links.count())

        objects_and_annotations = {}
        i = 1
        for link in links:
            self._log(
                'Processing link '
                + str(i) + '/' + total
                + ': Looking for annotations from ' + link.get_caller().get_fullname(), 'debug')
            i = i + 1

            if link.get_caller() in methods_to_search_in:
                if annotations_to_exclude is not None and link.get_callee().get_fullname() in annotations_to_exclude:
                    continue
                self._log(
                    'Object ' + link.get_caller().get_fullname() + ' also has annotation ' + link.get_callee().get_fullname())
                if link.get_caller() in objects_and_annotations:
                    objects_and_annotations[link.get_caller()].append(link.get_callee())
                else:
                    objects_and_annotations[link.get_caller()] = []
                    objects_and_annotations[link.get_caller()].append(link.get_callee())

        return objects_and_annotations

    def _create_links(self, application, objects_using_guice_with_their_annotations):
        """
        @type application: cast.application.Application
        """

        count_link_created = 0

        # Find all potential callees for our link, i.e methods annotated with @Provides
        potential_callees = self._find_methods_using_an_annotation(application, ['com.google.inject.Provides'])

        for caller, annotations in objects_using_guice_with_their_annotations.items():
            # Find the callees
            for annotation in annotations:
                self._log('Searching for a Provider for annotation '
                          + annotation.get_fullname()
                          + ' used in '
                          + caller.get_fullname())

                # Find all methods that link to the same annotation
                links = application.links().has_caller(potential_callees).has_callee([annotation])

                for l in links:
                    if l.get_caller().get_fullname() is not caller.get_fullname():
                        # Create a new link from our caller to this identified callee
                        new_link = create_link('useLink', caller, l.get_caller())
                        count_link_created = count_link_created + 1
                        self._log('Provider found, link created between '
                                  + caller.get_fullname()
                                  + ' and '
                                  + l.get_caller().get_fullname())
                        # TODO bookmark management? use the exact annotation bookmark for the link
                        # new_link.add_bookmark(src.get_positions())

        self._log(str(count_link_created) + ' links created in total')

    def _log(self, msg, level='info'):
        msg = '[com.castsoftware.uc.guice] ' + msg
        if level == 'info':
            logging.info(msg)
        elif level == 'debug':
            logging.debug(msg)
        elif level == 'warning':
            logging.warning(msg)
        elif level == 'error':
            logging.error(msg)
        else:
            logging.info(msg)
