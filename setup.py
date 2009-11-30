from setuptools import setup, find_packages
from os.path import join, dirname

version = 0.1
short_description = "Git cherry pick tracking."
long_description = open(join(dirname(__file__), "README.txt"), "r").read()

setup(name = "git_origin",
      version = version,
      description = short_description,
      long_description = long_description,
      classifiers = [], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords = "",
      author = "Chris Larson",
      author_email = "clarson@kergoth.com",
      url = "",
      license = "GPL v2",
      packages = find_packages("src"),
      package_dir = {"": "src"},
      namespace_packages = ["git_origin"],
      include_package_data = True,
      zip_safe = False,
      install_requires = [
          "setuptools",
          "GitPython",
      ],
)
