from multiprocessing.pool import ThreadPool
import logging

from .. import entities, utilities, PlatformException


class Ontologies:
    """
    Ontologies repository
    """

    def __init__(self, client_api, recipe):
        self.logger = logging.getLogger('dataloop.repositories.ontology')
        self.client_api = client_api
        self.recipe = recipe

    def create(self, labels, project_ids=None, attributes=None):
        """
        Create a new ontology

        :param labels: recipe tags
        :param project_ids: recipe project/s
        :param attributes: recipe attributes
        :return: Ontology object
        """
        if attributes is None:
            attributes = list()
        if project_ids is None and self.recipe is not None:
            project_ids = [self.recipe.dataset.project.id]
        elif not isinstance(project_ids, list):
            project_ids = [project_ids]
        # convert to platform label format (root)
        if isinstance(labels, dict):
            labels = self.labels_to_roots(labels)
        payload = {'roots': labels, 'projectIds': project_ids, 'attributes': attributes}
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/ontologies',
                                                        json_req=payload)
        if success:
            self.logger.info('Ontology was created successully')
            ontology = entities.Ontology.from_json(_json=response.json(), client_api=self.client_api,
                                                   recipe=self.recipe)
        else:
            self.logger.exception('Failed to create Ontology')
            raise PlatformException(response)
        return ontology

    def list(self):
        """
        List ontologies for recipe

        """
        if self.recipe is None:
            raise ('400', 'Action is not permitted')

        ontologies = [ontology_id for ontology_id in self.recipe.ontologyIds]

        def get_single_ontology(w_i_ontology):
            ontologies[w_i_ontology] = self.get(ontology_id=ontologies[w_i_ontology])

        pool = ThreadPool(processes=32)
        for i_ontology in range(len(ontologies)):
            pool.apply_async(get_single_ontology, kwds={'w_i_ontology': i_ontology})
        pool.close()
        pool.join()
        pool.terminate()

        return utilities.List(ontologies)

    def get(self, ontology_id):
        """
        Get Ontology object

        :param ontology_id: ontology id
        :return: Ontology object
        """
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/ontologies/%s' % ontology_id)
        if success:
            ontology = entities.Ontology.from_json(_json=response.json(), client_api=self.client_api,
                                                   recipe=self.recipe)
        else:
            self.logger.exception('Unable to get info for ontology. Ontology id: %s' % ontology_id)
            raise PlatformException(response)
        return ontology

    def delete(self, ontology_id):
        """
        Delete Ontology from platform

        :param ontology_id: ontology_id id
        :return: True
        """
        success, response = self.client_api.gen_request(req_type='delete',
                                                        path='/ontologies/%s' % ontology_id)
        if success:
            self.logger.debug('Ontology was deleted successfully')
            return success
        else:
            self.logger.exception('Failed to delete ontology')
            raise PlatformException(response)

    def update(self, ontology, system_metadata=False):
        """
        Update Ontology metadata

       :param ontology: Ontology object
       :param system_metadata: bool
       :return: Ontology object
       """
        url_path = '/ontologies/%s' % ontology.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='put',
                                                        path=url_path,
                                                        json_req=ontology.to_json())
        if success:
            self.logger.debug('Ontology was updated successfully')
            # update dataset labels
            ontology = entities.Ontology.from_json(_json=response.json(), client_api=self.client_api,
                                                   recipe=self.recipe)
            self.recipe.dataset.labels = ontology.labels
            return ontology
        else:
            self.logger.exception('Failed to update ontology')
            raise PlatformException(response)

    def labels_to_roots(self, labels):
        """
        Converts labels dict to a list of platform represantation of labels

        :param labels: labels dict
        :return: platform represantation of labels
        """
        roots = list()
        for label, color in labels.items():
            roots.append({'value': {
                "tag": label,
                "color": color,
                "attributes": []
            },
                'children': []
            })
        return roots
