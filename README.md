# CacheSimulation

ports in each components:

Racks: <br />
  port 0 connect to rack <br />
ToRs: <br />
  port 0 connect to racks <br />
  port 1,.... connect to aggregations <br />
Aggregations: <br />
  port 0 connect to controller switch <br />
  port 1 connect to Destination <br />
  port 2,.... connect to ToRs <br />
Controller Switch: <br />
  port 0 connect to controller <br />
  port 1,.... connect to aggregations <br />
Controller: <br />
  connect to controller switch <br />
