FROM ubuntu:latest

# Update packages and install necessary dependencies
RUN apt-get update
RUN apt-get install python3 -y

# Make the directory
RUN mkdir nebdeb

# Set the working directory
WORKDIR nebdeb

# Expose port (if required)
# EXPOSE 8080

# Specify the command to run the Python application
CMD ["/usr/bin/python3", "./nebdeb.py"]