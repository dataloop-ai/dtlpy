# **DTLPY – SDK and CLI for Dataloop.ai**

![logo.svg](docs%2F_static%2Flogo.svg)

[![Documentation Status](https://readthedocs.org/projects/dtlpy/badge/?version=latest)](https://sdk-docs.dataloop.ai/en/latest/?badge=latest)
[![PyPI Version](https://img.shields.io/pypi/v/dtlpy.svg)](https://pypi.org/project/dtlpy/)
[![Python Versions](https://img.shields.io/pypi/pyversions/dtlpy.svg)](https://github.com/dataloop-ai/dtlpy)
[![License](https://img.shields.io/github/license/dataloop-ai/dtlpy.svg)](https://github.com/dataloop-ai/dtlpy/blob/master/LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/dtlpy?period=total&units=international_system&left_color=grey&right_color=green&left_text=Downloads)](https://pepy.tech/project/dtlpy)

📚 [Platform Documentation](https://dataloop.ai/docs) | 📖 [SDK Documentation](https://sdk-docs.dataloop.ai/en/latest/) | [Developer docs](https://developers.dataloop.ai/)

An open-source SDK and CLI toolkit to interact seamlessly with the [Dataloop.ai](https://dataloop.ai/) platform, providing powerful data management, annotation capabilities, and workflow automation.

---

## **Table of Contents**

- [**DTLPY – SDK and CLI for Dataloop.ai**](#dtlpy--sdk-and-cli-for-dataloopai)
  - [**Table of Contents**](#table-of-contents)
  - [**Overview**](#overview)
  - [**Installation**](#installation)
  - [**Usage**](#usage)
    - [**SDK Usage**](#sdk-usage)
    - [**CLI Usage**](#cli-usage)
  - [**Python Version Support**](#python-version-support)
  - [**Development**](#development)
  - [**Resources**](#resources)
  - [**Contribution Guidelines**](#contribution-guidelines)

---

## **Overview**

DTLPY provides a robust Python SDK and a powerful CLI, enabling developers and data scientists to automate tasks, manage datasets, annotations, and streamline workflows within the Dataloop platform.

---

## **Installation**

Install DTLPY directly from PyPI using pip:

```bash
pip install dtlpy
```

Alternatively, for the latest development version, install directly from GitHub:

```bash
pip install git+https://github.com/dataloop-ai/dtlpy.git
```

---

## **Usage**

### **SDK Usage**

Here's a basic example to get started with the DTLPY SDK:

```python
import dtlpy as dl

# Authenticate
dl.login()

# Access a project
project = dl.projects.get(project_name='your-project-name')

# Access dataset
dataset = project.datasets.get(dataset_name='your-dataset-name')
```

### **CLI Usage**

DTLPY also provides a convenient command-line interface:

```bash
dlp login
dlp projects ls
dlp datasets ls --project-name your-project-name
```

---

## **Python Version Support**

DTLPY supports multiple Python versions as follows:

| Python Version      | 3.14 | 3.13 | 3.12 | 3.11 | 3.10 | 3.9 | 3.8 | 3.7 |
|---------------------|------|------|------|------|------|-----|-----|-----|
| **dtlpy >= 1.118**  | ✅   | ✅   | ✅   | ✅   | ✅   | ❌  | ❌  | ❌  |
| **dtlpy 1.99–1.117**| ❌   | ❌   | ❌   | ✅   | ✅   | ✅  | ✅  | ✅  |
| **dtlpy 1.76–1.98** | ❌   | ❌   | ❌   | ✅   | ✅   | ✅  | ✅  | ✅  |
| **dtlpy >= 1.61**   | ❌   | ❌   | ❌   | ❌   | ✅   | ✅  | ✅  | ✅  |
| **dtlpy 1.50–1.60** | ❌   | ❌   | ❌   | ❌   | ❌   | ✅  | ✅  | ✅  |

---

## **Development**

To set up the development environment, clone the repository and install dependencies:

```bash
git clone https://github.com/dataloop-ai/dtlpy.git
cd dtlpy
pip install -r requirements.txt
```

## **Resources**

- [Dataloop Platform](https://console.dataloop.ai)
- [Full SDK Documentation](https://sdk-docs.dataloop.ai/en/latest/)
- [Platform Documentation](https://dataloop.ai/docs)
- [SDK Examples and Tutorials](https://github.com/dataloop-ai/dtlpy-documentation)
- [Developer docs](https://developers.dataloop.ai/)

---

## **Contribution Guidelines**

We encourage contributions! Please ensure:

- Clear and descriptive commit messages
- Code follows existing formatting and conventions
- Comprehensive tests for new features or bug fixes
- Updates to documentation if relevant

Create pull requests for review. All contributions will be reviewed carefully and integrated accordingly.