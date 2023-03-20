import behave
import numpy as np
from time import sleep


@behave.given(u'I upload "{annotation_type}" annotation to the image item')
def step_impl(context, annotation_type):
    # Used to get item height and width from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    mask = None
    if annotation_type == "semantic segmentation":
        mask = np.zeros(shape=(context.item.height, context.item.width), dtype=np.uint8)
        mask[50:50, 150:200] = 1

    annotations_definitions_list = {
        "classification": context.dl.Classification(
            label="label1",
            attributes=[{"attributes1": "classification1"}]
        ),
        "point": context.dl.Point(
            x=10,
            y=10,
            label="label1",
            attributes=[{"attributes1": "point1"}]
        ),
        "box": context.dl.Box(
            left=50,
            top=50,
            right=100,
            bottom=100,
            label="label1",
            attributes=[{"attributes1": "box1"}]
        ),
        "rotated box": context.dl.Box(
            left=50,
            top=50,
            right=100,
            bottom=100,
            angle=45,
            label="label1",
            attributes=[{"attributes1": "box1"}]
        ),
        "cube": context.dl.Cube(
            front_bl=[50, 100],
            front_br=[100, 100],
            front_tr=[100, 50],
            front_tl=[50, 50],
            back_bl=[25, 75],
            back_br=[75, 75],
            back_tr=[75, 25],
            back_tl=[25, 25],
            label="label1",
            attributes=[{"attributes1": "cube1"}]
        ),
        "semantic segmentation": context.dl.Segmentation(
            geo=mask,
            label="label1",
            attributes=[{"attributes1": "semantic1"}]
        ),
        "polygon": context.dl.Polygon(
            geo=[[25, 25], [50, 100], [70, 10]],
            label="label1",
            attributes=[{"attributes1": "polygon1"}]
        ),
        "polyline": context.dl.Polyline(
            geo=[[25, 25], [50, 100], [70, 10]],
            label="label1",
            attributes=[{"attributes1": "polyline1"}]
        ),
        "ellipse": context.dl.Ellipse(
            x=100,
            y=100,
            rx=50,
            ry=75,
            angle=0,
            label="label1",
            attributes=[{"attributes1": "ellipse1"}]
        ),
        "note": context.dl.Note(
            left=50,
            top=50,
            right=100,
            bottom=100,
            label="label1",
            attributes=[{"attributes1": "note1"}],
            assignee=context.dl.info()['user_email'],
            creator=context.dl.info()['user_email']
        )
    }

    builder = context.item.annotations.builder()
    builder.add(annotations_definitions_list[annotation_type])
    context.annotation = context.item.annotations.upload(annotations=builder)[0]


@behave.given(u'I upload "{annotation_type}" annotation with description "{annotation_description}" to the image item')
def step_impl(context, annotation_type, annotation_description):
    # Used to get item height and width from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    mask = np.zeros(shape=(context.item.height, context.item.width), dtype=np.uint8)
    mask[50:50, 150:200] = 1

    annotations_definitions_list = {
        "classification": context.dl.Classification(
            label="label1",
            attributes=[{"attributes1": "classification1"}],
            description=annotation_description
        ),
        "point": context.dl.Point(
            x=10,
            y=10,
            label="label1",
            attributes=[{"attributes1": "point1"}],
            description=annotation_description
        ),
        "box": context.dl.Box(
            left=50,
            top=50,
            right=100,
            bottom=100,
            label="label1",
            attributes=[{"attributes1": "box1"}],
            description=annotation_description
        ),
        "rotated box": context.dl.Box(
            left=50,
            top=50,
            right=100,
            bottom=100,
            angle=45,
            label="label1",
            attributes=[{"attributes1": "box1"}],
            description=annotation_description
        ),
        "cube": context.dl.Cube(
            front_bl=[50, 100],
            front_br=[100, 100],
            front_tr=[100, 50],
            front_tl=[50, 50],
            back_bl=[25, 75],
            back_br=[75, 75],
            back_tr=[75, 25],
            back_tl=[25, 25],
            label="label1",
            attributes=[{"attributes1": "cube1"}],
            description=annotation_description
        ),
        "semantic segmentation": context.dl.Segmentation(
            geo=mask,
            label="label1",
            attributes=[{"attributes1": "semantic1"}],
            description=annotation_description
        ),
        "polygon": context.dl.Polygon(
            geo=[[25, 25], [50, 100], [70, 10]],
            label="label1",
            attributes=[{"attributes1": "polygon1"}],
            description=annotation_description
        ),
        "polyline": context.dl.Polyline(
            geo=[[25, 25], [50, 100], [70, 10]],
            label="label1",
            attributes=[{"attributes1": "polyline1"}],
            description=annotation_description
        ),
        "ellipse": context.dl.Ellipse(
            x=100,
            y=100,
            rx=50,
            ry=75,
            angle=0,
            label="label1",
            attributes=[{"attributes1": "ellipse1"}],
            description=annotation_description
        ),
        "note": context.dl.Note(
            left=50,
            top=50,
            right=100,
            bottom=100,
            label="label1",
            attributes=[{"attributes1": "note1"}],
            assignee=context.dl.info()['user_email'],
            creator=context.dl.info()['user_email'],
            description=annotation_description
        )
    }

    builder = context.item.annotations.builder()
    builder.add(annotations_definitions_list[annotation_type])
    context.annotation = context.item.annotations.upload(annotations=builder)[0]
