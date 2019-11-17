import logging
import traceback

from .. import entities, miscellaneous, PlatformException

logger = logging.getLogger(name=__name__)


class Ontologies:
    """
    Ontologies repository
    """

    def __init__(self, client_api, recipe):
        self._client_api = client_api
        self._recipe = recipe

    @property
    def recipe(self):
        assert isinstance(self._recipe, entities.Recipe)
        return self._recipe

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
        if project_ids is None and self._recipe is not None:
            project_ids = [self.recipe.dataset.project.id]
        elif not isinstance(project_ids, list):
            project_ids = [project_ids]
        # convert to platform label format (root)
        labels = self.labels_to_roots(labels)
        payload = {"roots": labels,
                   "projectIds": project_ids,
                   "attributes": attributes}
        success, response = self._client_api.gen_request(req_type="post",
                                                         path="/ontologies",
                                                         json_req=payload)
        if success:
            logger.info("Ontology was created successfully")
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
        else:
            logger.exception("Failed to create Ontology")
            raise PlatformException(response)
        return ontology

    def list(self):
        """
        List ontologies for recipe

        :return:
        """
        if self._recipe is None:
            raise ("400", "Action is not permitted")

        ontologies = [ontology_id for ontology_id in self.recipe.ontologyIds]

        pool = self._client_api.thread_pool_entities
        jobs = [None for _ in range(len(ontologies))]
        for i_ontology, ontology_id in enumerate(ontologies):
            jobs[i_ontology] = pool.apply_async(self._protected_get, kwds={'ontology_id': ontology_id})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _protected_get(self, ontology_id):
        """
        Same as get but with try-except to catch if error
        :param ontology_id:
        :return:
        """
        try:
            ontology = self.get(ontology_id=ontology_id)
            status = True
        except:
            ontology = traceback.format_exc()
            status = False
        return status, ontology

    def get(self, ontology_id):
        """
        Get Ontology object

        :param ontology_id: ontology id
        :return: Ontology object
        """
        success, response = self._client_api.gen_request(req_type="get",
                                                         path="/ontologies/{}".format(ontology_id))
        if success:
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
        else:
            raise PlatformException(response)
        return ontology

    def delete(self, ontology_id):
        """
        Delete Ontology from platform

        :param ontology_id: ontology_id id
        :return: True
        """
        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="/ontologies/%s" % ontology_id)
        if success:
            logger.debug("Ontology was deleted successfully")
            return success
        else:
            raise PlatformException(response)

    def update(self, ontology, system_metadata=False):
        """
        Update Ontology metadata

       :param ontology: Ontology object
       :param system_metadata: bool
       :return: Ontology object
       """
        url_path = "/ontologies/%s" % ontology.id
        if system_metadata:
            url_path += "?system=true"
        success, response = self._client_api.gen_request(req_type="put",
                                                         path=url_path,
                                                         json_req=ontology.to_json())
        if success:
            logger.debug("Ontology was updated successfully")
            # update dataset labels
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
            self.recipe.dataset._labels = ontology.labels
            return ontology
        else:
            logger.exception("Failed to update ontology:")
            raise PlatformException(response)

    @staticmethod
    def labels_to_roots(labels):
        """
        Converts labels dict to a list of platform representation of labels

        :param labels: labels dict
        :return: platform representation of labels
        """
        roots = list()
        if isinstance(labels, dict):
            for label in labels:
                root = {
                    "value": {
                        "tag": label,
                        "color": labels[label],
                        "attributes": list(),
                    },
                    "children": list(),
                }
                roots.append(root)
        elif isinstance(labels, list):
            for label in labels:
                if isinstance(label, entities.Label):
                    root = label.to_root()
                elif "value" in label:
                    root = {
                        "value": label["value"],
                        "children": label.get("children", list()),
                    }
                else:
                    root = {
                        "value": {
                            "tag": label.get("tag", None),
                            "color": label.get("color", "#FFFFFF"),
                            "attributes": label.get("attributes", list()),
                        },
                        "children": label.get("children", list()),
                    }
                roots.append(root)
        for root in roots:
            if not isinstance(root["value"]["color"], str):
                root["value"]["color"] = "#%02x%02x%02x" % root["value"]["color"]
        return roots
