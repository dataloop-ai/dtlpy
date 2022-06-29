import behave, os, json
import time


@behave.when(u'I add "{input_type}" attribute to ontology')
def step_impl(context, input_type):
    if input_type == 'checkbox':
        att_type = context.dl.AttributesTypes.CHECKBOX
    elif input_type == 'radio_button':
        att_type = context.dl.AttributesTypes.RADIO_BUTTON
    elif input_type == 'slider':
        att_type = context.dl.AttributesTypes.SLIDER
    elif input_type == 'yes_no':
        att_type = context.dl.AttributesTypes.YES_NO
    elif input_type == 'free_text':
        att_type = context.dl.AttributesTypes.FREE_TEXT

    scope = optional = multi = values = attribute_range = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "title":
            title = param[1]
        elif param[0] == "key":
            key = param[1]
        elif param[0] == "scope":
            if param[1].startswith('['):
                param[1] = eval(param[1])
            elif param[1] == 'all':
                param[1] = '*'
            scope = param[1]
        elif param[0] == "optional":
            optional = eval(param[1])
        elif param[0] == "multi":
            multi = eval(param[1])
        elif param[0] == "values":
            if param[1].startswith('['):
                param[1] = eval(param[1])
            values = param[1]
        elif param[0] == "attribute_range":
            att_range = param[1].split(',')
            param[1] = context.dl.AttributesRange(min_range=int(att_range[0]), max_range=int(att_range[1]), step=int(att_range[2]))
            attribute_range = param[1]

    try:
        context.ontology.update_attributes(title=title,
                                           key=key,
                                           attribute_type=att_type,
                                           scope=scope,
                                           optional=optional,
                                           multi=multi,
                                           values=values,
                                           attribute_range=attribute_range)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'I validate attribute "{input_type}" added to ontology')
def step_impl(context, input_type):
    context.ontology = context.recipe.ontologies.get(ontology_id=context.recipe.ontology_ids[0])

    if input_type == 'checkbox':
        att_type = context.dl.AttributesTypes.CHECKBOX
    elif input_type == 'radio_button':
        att_type = context.dl.AttributesTypes.RADIO_BUTTON
    elif input_type == 'slider':
        att_type = context.dl.AttributesTypes.SLIDER
    elif input_type == 'yes_no':
        att_type = context.dl.AttributesTypes.YES_NO
    elif input_type == 'free_text':
        att_type = context.dl.AttributesTypes.FREE_TEXT

    assert att_type in [att['type'] for att in context.ontology.to_json()['metadata']['attributes']], "TEST FAILED: {} not in Ontology attributes".format(att_type)


@behave.then(u'I delete attributes with key "{input_type}" in ontology')
def step_impl(context, input_type):
    context.ontology.delete_attributes(keys=input_type)


@behave.then(u'I delete all attributes in ontology')
def step_impl(context):
    context.ontology = context.recipe.ontologies.get(ontology_id=context.recipe.ontology_ids[0])
    all_keys = [att['key'] for att in context.ontology.to_json()['metadata']['attributes']]
    context.ontology.delete_attributes(keys=all_keys)

    context.ontology = context.recipe.ontologies.get(ontology_id=context.recipe.ontology_ids[0])
    assert context.ontology.to_json()['metadata']['attributes'] == [], "TEST FAILED: Not all attributes are deleted.\n{}".format(context.ontology.to_json()['metadata']['attributes'])
