import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
     name='PlumedToHTML',  
     version='0.1',
     author="Gareth Tribello",
     author_email="gareth.tribello@gmail.com",
     description="A package for creating pretified HTML for PLUMED files",
     long_description=README,
     long_description_content_type="text/markdown",
     url="https://github.com/plumed/PlumedToHTML.git",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: Freely Distributable",
         "Operating System :: OS Independent",
     ],
 )
