import behave
from time import sleep


@behave.given(u'I upload "{annotation_type}" annotation to the video item')
def step_impl(context, annotation_type):
    # Used to get item data from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

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
    builder.add(annotations_definitions_list[annotation_type], object_id=1, frame_num=5, end_frame_num=10, fixed=False)
    context.annotation = context.item.annotations.upload(annotations=builder)[0]


@behave.given(u'I upload "{annotation_type}" annotation with description "{annotation_description}" to the video item')
def step_impl(context, annotation_type, annotation_description):
    # Used to get item data from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

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
    builder.add(annotations_definitions_list[annotation_type], object_id=1, frame_num=5, end_frame_num=10, fixed=False)
    context.annotation = context.item.annotations.upload(annotations=builder)[0]
