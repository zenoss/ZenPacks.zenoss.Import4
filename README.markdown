ZenPacks.zenoss.Import4
=======================
When a user upgrades Zenoss 4.x to a 5.x environment, there is also a need to migrate the existing 4.x operating data to the 5.x environment.  This zenpack provides the back-end of the migration functionalities. 

When the ZenPack is installed in the 5.x environment, it provides two control-center services. The migration functionalities are encapsulated into the service run commands defined in these two services - `imp4mariadb` and `imp4opentsdb`.

The back-end is implemented by a set of python programs and shell scripts. `flock` over NFS is used to control flow synchronization.

The migration process includes three logical classes of operations listed below - events archive, Models, and performance data. 

Events archive
--------------
Event migration is relatively straightforward. The related event database and index are first extracted from the back-up file from the 4.x application. There contents are imported directly into the 5.x database, i.e.  `zenoss_zep`.

* related imp4mariadb service commands:
```
events-database - import the zenoss_zep event database
events-index - copy the zep_index
```

Models
------
zodb keeps the model object data. Note that the model object data must be restored and migrated in order. 
* related imp4mariadb service commands:
```
model-database - import the zodb model object database
model-catalog - copy the global catalog index
model-zenmigrate - migrate the database schema from 4.x to 5.x
model-zenpack - restore and upgrade where applicable the 4.x zenpacks to 5.x
```

Performance data
----------------
Performance data migration converts and imports the RRD time series data from the 4.x environment to the opentsdb data in the 5.x environment. Because there is no dependency between the performance data import to the models or events data, this can be done at any stage. However, because all the migration operations are done on the same host, importing the performance data and stressing the opentsdb stack can destablize hbase/region server/zookeeper. Thus, the performance data migration should be delayed until both the models and events migrations are completed as shown in the sequences below.


```
1
|------------------------------------>|
|events-database                      |
|                                     |
|------------------------------------>|
|events-index                         |----------------->|----------------->|
|                                     |model-zenmigrate  3  model-zenpack   4
|------------------------------------>|
|model-database                       |
|                                     |
|------------------------------------>|
|model-catalog                        2
  `perf-import` starts at the end phase to reduce opentsdb pipeline stress  |------>|
                                      perf-import (to infinity, and beyond) 4 
|
1
```

* related imp4mariadb service command:
```
perf-import - the main interface to start the performance data migration process. It dispatches the rrd files into tasks that can be converted and imported by the following two types of workers.
```

 * start imp4mariadb service:
This service provides the RRD to opentsdb conversion script - `imp4mariadb.sh`. This service is designed to run with multiple instances in parallel when computational resource allows.
```
serviced service shell ${SERVICED_MOUNT_OPT} imp4mariadb bash -c /import4/pkg/bin/imp4mariadb.sh
```

 * start imp4opentsdb service:
This service provides the opentsdb data import script - `imp4opentsdb.sh`. This service is designed to run with multiple instances in parallel when computational resource allows.
```
serviced service shell ${SERVICED_MOUNT_OPT} imp4opentsdb bash -c /import4/pkg/bin/imp4opentsdb.sh
```

Back-end storage management
------------------
* other imp4mariadb service command:
```
check - checks the integrity of the migration data file. It extracts its content at the same directory, the current directory of execution, as the input file. The current directory must be world read-writable.
```
In addition to the use of `${PWD}`, which is automatically mounted into the container as `/mnt/pwd`, the back-end implementation is also structured around a shared space `/import4`. It must be mounted into both services, `imp4mariadb` and `imp4opentsdb`. `/import4` mainly keeps the extracted performance data as well as keeps its intermediate migration results. This '/import4` space must be supplied by the user and mounted into the containers via `${SERVICED_MOUNT_OPT}`.

If `/import4` space is not mounted by the user, the container will consume the more limited dfs space of the `imp4mariadb` service.

Managing the migration data
---------------------------
The export4 utility, to be run on the Zenoss 4.x environment, packages the migration data into a migration data file. The user puts the migration data file in a directory where the content can be accessed by the 5.x service commands. The migration data file basically contains a backup file generated by the 4.x zenbackup command plus additional 4.x information required for migration.

Before the migration can start on the 5.x environment, the user must prepare the service images first by calling -
```
serviced service run imp4mariadb initialize
```

`initialize` command installed the required utility, such as rrdtools and others, into the 5.x image. It also prepares the working space, `/import4`, for subsequent migration operations.

After the shared working space is prepared, the user can then ask the `check` service command to check and extract the migration data file. At this point, the content of the data file is extracted and examined for correctness.

```
cd <working_dir>    # a world-readwritable directory keeping the migration backup <filename.tar>
serviced service run imp4mariadb check <filename.tar>
```
Once all the migration data is in place, the migration sequences can be started in parallel as illustrated by the graph above.

Migration data flow
-------------------

The diagram shows the life-cycle of the migration data from 4.x to 5.x environment.
```
4.x             migration data file             5.x
export4.py ---> 4x-backup.tar                   initialize
                +----------------------------+
                | zenbackup_4x.tgz:          |
                | +------------------------+ |
                | |zep.sql.gz              | |
                | |zep.tar                 | |
                | |zodb.sql.gz             | |
                | |zencatalogservice.tar   | |
                | |ZenPacks.tar            | |
                | |perf.tar.gz             | |
                | +------------------------+ |
                | md5                        |
                | componentList.txt          |
                | dmd_uuid.txt               |
                | flexera license            |
                | rrdpath.map                |
                +----------------------------+  
                                |
                                +-------------> /mnt/pwd 
                                                check -+-> /mnt/pwd/<extracted files>
                                                       +---> /import4/staging/<performance data>
                                                                    |
                                                event-database      |
                                                event-index         |
                                                                    |
                                                model-database      |
                                                model-catalog       |
                                                model-zenmigrate    |
                                                model-zenpack       |
                                                                    V
                                                perf-import -+-> converter    +----------+
                                                             +-> importer --> | opentsdb |
                                                                              +----------+
```
