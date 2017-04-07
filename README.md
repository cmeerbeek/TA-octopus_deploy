# Splunk TA for Octopus Deploy

The Splunk TA for Octopus Deploy is a technology add-on for retrieving data from a Octopus Deployment installation. This Add-On only provides a Modular Input and related configuration files. 

## Getting Started

You must have an installed and configured Octopus application to complete the setup process of this app.

### Used libraries

Splunklib which originates from the Splunk Software Development Kit for Python. The Splunk Software Development Kit for Python is licensed under the [Apache
License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html).

For compatibility with Python 2.#, The Splunk Software Development Kit
for Python ships with ordereddict.py from the ordereddict package on
[PyPI](http://pypi.python.org/pypi/ordereddict/1.1), which is licensed
under the MIT license (see the top of bin/splunklib/ordereddict.py).

### Install Prerequisites

Too make sure everything works correctly make sure the following is available and working:

1. A working Octopus application
2. Access to the REST API port on the Octopus server from a Heavy Forwarder or Splunk single instance (port 80 for HTTP and port 443 for HTTP or else if configured differently)
3. An API key to retrieve data from Octopus. See [Octopus Wiki](https://github.com/OctopusDeploy/OctopusDeploy-Api/wiki).
4. A Splunk Heavy Forwarder or Single Instance with Splunk 6.0.x or higher running on Linux or Unix or OS X.

### Install instructions

Installation of the apps can be done using the Splunk UI as explained below or manually be extracting the add-on to the $SPLUNK_HOME/etc/apps folder. 

**Install using Splunk UI:**

1. Select "Manage Apps" from the Apps dropdown.
2. Select the "Install app from file" button.
3. Select the generated `TA-octopus_deploy.spl` package.
4. Go to Settings -> Data Inputs -> Octopus Deploy API to add inputs.

**Configure the TA**

The TA will not deliver predefined inputs for now so you need to configure each inputs manually. Go to Settings -> Data Inputs -> Octopus Deploy API to start configuring Inputs.

When you press "New" the Input Wizard will start and you will see one screen with multiple fields.

1. Name > The name for Input in the Splunk UI (e.g. Octopus Users)
2. Endpoint > The Octopus endpoint to access (e.g. users)
2. Hostname > The protocol, hostname and port on which Octopus Deploy is listening (e.g. http://octopus.example.com:8080)
5. Password > The API key needed for authentication with the API. See [Octopus Wiki](https://github.com/OctopusDeploy/OctopusDeploy-Api/wiki). 
6. Confirm password > The API key needed for authentication with the API.
7. Use check pointing > If you do not want to index all the data inside each time the Input is running enable check pointing. The Input will keep track of the last indexed record and will only index new records.
8. Interval > Configure the interval on which the Input needs to run. 

Check "More Settings" to configure Sourcetype, Host and Index.

The following list show the most common endpoints for Octopus Deploy API and if check pointing should be applied:
* machines (use check pointing: NO)
* projects (use check pointing: NO)
* releases (use check pointing: YES)
* deployments (use check pointing: YES)
* events (use check pointing: YES)
* environments (use check pointing: NO)
* users (use check pointing: NO)
* tasks (use check pointing: YES)

See [Octopus Wiki](https://github.com/OctopusDeploy/OctopusDeploy-Api/wiki) for more information on the available endpoints.

## ChangeLog

See [CHANGELOG](CHANGELOG.md) for details.

## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Added some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request

## Support

This app is developed in the open at [GitHub](https://github.com/cmeerbeek/TA-octopus_deploy). Use that repository-page to file issues if you have questions or need support.

## ToDo

* Rebuild Add-on using Splunk Add-on Builder so the TA will confirm to Splunk best practices and uses a nice UI for configuring inputs

## Copyright

 Copyright (c) 2017 Coen Meerbeek. See [LICENSE](LICENSE) for details.
