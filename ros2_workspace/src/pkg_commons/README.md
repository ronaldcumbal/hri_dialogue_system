## Compiling source

Both catkin-pkg and lark will be required to compile the source files:

`pip install catkin_pkg`

`pip install lark`

There is a problem with the libraries `em` and `emPY` as they both use the same namespace. Start by removing both:

`pip uninstall em`

`pip uninstall empy`

And then install this version of `emPY`:

`pip install empy==3.3.4`


## MSG and SRV Name:

Follow requirements: [Source](https://robotics.stackexchange.com/questions/100382/how-should-i-name-my-message-file)

- Start with capital letter
