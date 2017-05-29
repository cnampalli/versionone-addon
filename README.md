# Devops VersionOne Addon

## Configuration

There are 2 different ways of configuring the add-on. You can use the setup from within the add-on or use a configuration file and generate the inputs.conf before installing the add-on as described below.

* Configure the *config.properties* with the following properties :
  
  - host : URL of the VersionOne server 
  - protocol : Protocole to access API (ex : https)
  - auth_type : Type of authentication used to access the server (ex :basic)
  - auth_user : Username used to log in
  - auth_password : Password used to log in
  - project : Project to query for
  - response_handler : VersionOneQuery or VersionOne depending on the api you want to use (cf. VersionOne rest documentation)
  
* Generate the final configuration :
  
    python generate_versionone_config.py <config>
    
* Check the *default/inputs.conf* generated has all of your configuration parameters

* You may add as many sections as you want to include different information or ping different servers, the category name of the config file **MUST** be different, it will not be used in the inputs.conf file so name it as you wish

```
[VersionOne-1]
host=www51.v1host.com
protocol=https
auth_type = custom
access_token = ********************
project=Project1
response_handler = VersionOneQuery


[VersionOne-2]
host=www52.v1host.com
protocol=https
auth_type = custom
access_token = *************
project=Project2
response_handler = VersionOne
```

## Package

* Create a tarball of this repository :

    tar czvf aaam-devops-versionone-addon.tar.gz aaam-devops-versionone-addon
    
## Installation 

* Upload this archive into splunk with the Manage Apps UI screen
* Don't forget to create the index **aaam_devops_versionone_idx** if it is not done

## Search 

* data is present in the **aaam_devops_versionone_idx** index

## Lookup tables
In order to provide a more readable output in Splunk, the following lookup tables are populated :
 - versionone_Scope.csv
 - versionone_StoryCategory.csv
 - versionone_StorySource.csv
 - versionone_StoryStatus.csv
 - versionone_Team.csv
 - versionone_Theme.csv
 - versionone_Timebox.csv
 - versionone_WorkitemRisk.csv

They provide a mapping between the VersionOne oid and their name.

The configuration for these is accessible in the VersionOneLookups Data inputs of your Splunk application server.
