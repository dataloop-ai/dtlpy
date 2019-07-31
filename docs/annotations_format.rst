Annotation Format
==================

Dataloop Annotation Format:
---------------------------
.. code-block:: python

    ##########
    # image: #
    ##########

    # box
    {
        "type": "box", # can be box/point/ellipse/binary/segment
        "label": "label",
        "attributes": [ # list of attributes
            "attr1",
            "attr2"
        ],
        "coordinates": [
            {
                "x": 236.43,
                "y": 349.45,
                "z": 0
            },
            {
                "x": 446.18,
                "y": 404.64,
                "z": 0
            }
        "metadata": {} # optional
    },

    # ellipse
    {
        "type": "ellipse",
        "label": "person",
        "attributes": [
            "attr1"
        ],
        "coordinates": {
            "center": {
                "x": 81.96402359213562,
                "y": 285.4436667373431,
                "z": 0
            },
            "rx": 106.50932425881204,
            "ry": 110.37094808321072,
            "angle": 0
        }
    },

    # polyline/polygon
    {
        "type": "segment",
        "label": "cat",
        "attributes": [],
        "coordinates": [[
            {
                "x": 229.19232006582055,
                "y": 232.74690570519735
            },
            {
                "x": 201.16548780201248,
                "y": 204.70182873323398
            },
            {
                "x": 211.1104927988476,
                "y": 190.22695029609156
            },
            {
                "x": 176.75502099159894,
                "y": 118.75723801270104
            },
            {
                "x": 121.60544782733136,
                "y": 129.61339684055784
            },
            {
                "x": 199.35730507531517,
                "y": 228.22350619359037
            }
        ]]
    },

    # point
    {
        "type": "point",
        "label": "dog",
        "attributes": [],
        "coordinates": {
            "x": 139.6872750943043,
            "y": 106.09171938020144,
            "z": 0
        }
    }

    #########
    # video #
    #########
    {
        "coordinates": [
            {
                "x": 1418.3333333333335,
                "y": 203.75000000000006,
                "z": 0
            },
            {
                "x": 1448.3490986687052,
                "y": 253.05219278209233,
                "z": 0
            }
        ],
        "metadata": {
            "system": {
                "frame": 0,
                "snapshots_": [
                    {
                        "frame": 5,
                        "label": "Home",
                        "attributes": [],
                        "type": "box",
                        "data": [
                            {
                                "x": 1411.5833333333335,
                                "y": 208.50000000000006,
                                "z": 0
                            },
                            {
                                "x": 1441.5990986687052,
                                "y": 257.80219278209233,
                                "z": 0
                            }
                        ]
                    },
                    {
                        "frame": 10,
                        "label": "Home",
                        "attributes": [],
                        "type": "box",
                        "data": [
                            {
                                "x": 1404.8333333333335,
                                "y": 213.25000000000006,
                                "z": 0
                            },
                            {
                                "x": 1434.8490986687052,
                                "y": 262.55219278209233,
                                "z": 0
                            }
                        ]
                    },
                    {
                        "frame": 15,
                        "label": "Home",
                        "attributes": [],
                        "type": "box",
                        "data": [
                            {
                                "x": 1398.0833333333335,
                                "y": 218.00000000000006,
                                "z": 0
                            },
                            {
                                "x": 1428.0990986687052,
                                "y": 267.30219278209233,
                                "z": 0
                            }
                        ]
                    }
                ],
                "automated": false
            },
            "user": {} # user metadata - optional
        },
        "label": "Home",
        "attributes": [],
        "type": "box"
    }

Annotation Convertors:
-----------------------
.. code-block:: python