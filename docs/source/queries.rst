Queries
=======

Using queries you can filter out items and get a generator of the filtered items.
Query entity help build such query

Query options:

.. code-block:: python

	{
	  "example_query": {
		"directories": [
		  "/some/dir",
		  "/",
		  "..."
		],
		"filenames": [
		  "/some/file.jpg",
		  "/item/in/directory",
		  "/",
		  "..."
		],
		"mimetypes": [
		  "image/jpeg",
		  "video/mp4",
		  "..."
		],
		"annotated": true,
		"itemMetadata": {
		  "my": {
			"metadata": {
			  "has": {
				"these": {
				  "field1": true,
				  "field2": 1
				}
			  }
			}
		  }
		},
		"labels": [
		  "dog",
		  "cat",
		  "..."
		],
		"annotationTypes": [
		  "box",
		  "binary",
		  null
		],
		"attributes": [
		  "1",
		  "2",
		  "..."
		],
		"creators": [
		  "assaf@dataloop.ai",
		  "john",
		  "some-org.com"
		],
		"annotationMetadata": {
		  "some": {
			"annotation": {
			  "metadata": {
				"is": true,
				"queried": "123"
			  }
			}
		  }
		}
	  }
	}
