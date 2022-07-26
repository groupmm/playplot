Exception Handling
==================

Exception handling across processes is challenging.
This package uses three ways to deal with it.

- All errors are getting written into stderr on the child processes.

- Child processes may display a error message box. (On per default in interactive sessions, like jupyter)

- We may check for exceptions in the main process by calling check on a session.
  This will raise an ForeignProcessException describing the first error which occurred.
  For more details see the api documentation.

An Exception in a plotting process closes the plot, while an exception in the audio process closes the whole session.