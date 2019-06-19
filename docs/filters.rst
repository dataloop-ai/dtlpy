Filters
=======

Using filters you can filter out items and get a generator of the filtered items.
Filters entity help build such filter

Filters options (or any combination of them):

.. code-block:: python

	Filters(directories=["/some/dir",
			     "/",])
	Filters(filenames=["/some/file.jpg",
		           "/item/in/directory",
			   "/"])
	Filters(mimetypes=["image/jpeg",
                           "video/mp4"])
	Filters(itemType="file"])
	Filters(itemMetadata={"my": {
		                  "metadata": {
				      "has": {
			                  "these": {
                                              "field1": true,
                                              "field2": 1
                                              }
				          }
				      }
		                  }
		              })
	Filters(labels=["dog",
			"cat"])
