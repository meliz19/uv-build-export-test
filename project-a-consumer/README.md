  As long as the editable dependencies are published first, the available packages' versions are retrieved and added to this package's wheel file. 
 ```
 uv build --no-sources --index "https://pypi.org/simple" --index "https://test.pypi.org/simple/"   
 ```


To export the dependencies, we can do the same thing...
 ```
 uv export --output-file ./requirements.txt --no-sources --no-editable
 ```