from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="Comments analyses",
    version="0.0.1",
    author="Lucas Brunschwig, Arthur Valentin",
    author_email="lucas.brunschwig@gmail.com",
    description="Part of mend-mi Lauzhack 2022",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.10"
    ],
)