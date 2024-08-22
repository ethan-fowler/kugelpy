### Generating Doxygen Documentation
In a conda environment you should be able to run
```shell
    conda install doxygen
```
With this package installed and active in your terminal instance, navigate to `/kugelpy/doxygen` and simply run 
```shell
    doxygen
```
This should detect `Doxyfile` which provides instructions to `doxygen` as it reads through `kugelpy`. It will automatically detect any formatted documentation and add it to an HTML project, which should save to the same folder. This folder can then be downloaded locally and the documentation can be seen in a web browser by opening `/html/index.html`.

### Editing Doxygen Documentation
Doxygen documentation generally takes two forms: variable documentation and bulk text documentation. When attempting to document a variable, locate that variable and leave a comment *above* it with two hashtags. 
```python
    ## (str, default: 'example') Here is the variable description
    variable = 'example'
```
Single hashtags are not read by doxygen as documentation unless following a comment with two hashtags.
```python
    # Not documentation

    ## Documentation
    # Also documentation
```
For variable descriptions spanning multiple lines (as this must be specified by the user), follow this format using new lines (`\n`)
```python
    ## Variable description \n
    ## continued description \n
    ## more description \n
    ## etc.
```
If this variable is a class parameter/attribute, doxygen will not include the variable type or default value in any kind of special format. For other variables, doxygen my automatically populate the type and default value (never tested). When commenting a function, documentation will generally look like this:
```python
    def myFunc(var1, var2, var3):
        '''!
        Here is a description of the function.

        @param var1     Description of var1
        @param var2     Description of var2
        @param var3     Description of var3

        @return         Whatever the function return.

        NOTES
        Any useful notes (can include Markdown formatting!)
        '''

        for i in range(len(var1)):
            ...
```
It is **very important** that the first three quotations are followed by an exclamation mark (!) as this signals to doxygen that the following comment should be included in documentation. Doxygen also accepts a header for a file/module following this format (for a python class named `class` found in `FileName.py`) which uses Markdown formatting
```python
    """! @brief Defines the sensor classes."""
    ##
    # @file FileName.py
    #
    # @brief Decription of module.
    #
    # @section description_class Description
    # Description of class
    # - class
    # - other_class_inheriting_from_class
    #
    # @section libraries_class Libraries/Modules
    # - library1
    #   - What library1 is used for
    # - library2
    #   - What library2 is used for
    #
    # @section notes_class Notes
    # - First comment
    # - Second comment
    # - etc.
    #
    # @section todo_class TODO
    # - List
    # - Of 
    # - Things
    # - To
    # - Do
    #
    # @section author_class Author(s)
    # - Created by John Woolsey on 05/27/2020.
    # - Modified by John Woolsey on 06/11/2020.
    #
    # Copyright (c) 2020 Woolsey Workshop.  All rights reserved.
```
For additional information, see https://www.woolseyworkshop.com/2020/06/25/documenting-python-programs-with-doxygen/.