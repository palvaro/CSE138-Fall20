# ------------------------------
# Run Docker containers
docker network create --subnet=10.10.0.0/16 kv_subnet
docker build -t kv-store:3.0 .
# example node addresses
addr1="10.10.0.4:13800"
addr2="10.10.0.5:13800"
addr3="10.10.0.6:13800"
# convenience variables
initial_full_view="${addr1},${addr2}"
full_view=${initial_full_view},${addr3}
# run three nodes
docker run --name="node1"        --net=kv_subnet     \
           --ip=10.10.0.4        -d -p 13801:13800   \
           -e ADDRESS="${addr1}"                     \
           -e VIEW=${initial_full_view}              \
           kv-store:3.0
docker run --name="node2"        --net=kv_subnet     \
           --ip=10.10.0.5        -d -p 13802:13800   \
           -e ADDRESS="${addr2}"                     \
           -e VIEW=${initial_full_view}              \
           kv-store:3.0
           
# node3 will not be added to the existing database until view-change, but we can initialize it here. 
docker run --name="node3"        --net=kv_subnet     \
           --ip=10.10.0.6        -d -p 13803:13800   \
           -e ADDRESS="${addr3}"                     \
           -e VIEW="${full_view}"                    \
           kv-store:3.0
           
sleep 5

python test_assignment3.py

docker kill node1 node2 node3
docker rm node1 node2 node3
