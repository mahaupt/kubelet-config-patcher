import os
import subprocess
import time
import json
import requests
import sys
import argparse
import re

parser = argparse.ArgumentParser(description='Patches k8s nodes with custom KubeletConfig settings')
parser.add_argument('-t', '--time', help="Time in seconds to wait between patching nodes", type=int, default=60)
parser.add_argument('--confirm', action='store_const', help="Applies KubeletConfig to all nodes", const=True, default=False)
args = parser.parse_args()

def getNodes():
    print("Get all nodes")
    nodes = os.popen("kubectl get nodes -o=custom-columns=NAME:.metadata.name").read().split("\n")
    del nodes[0]
    nodes.pop()
    return nodes

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def getKubeletConfig():
    print("Get kubeletconfig")
    ls_proxy=subprocess.Popen(["kubectl", "proxy", "--port=8002"])
    time.sleep(5) # wait for proxy to establish
    r=requests.get("http://localhost:8002/api/v1/nodes/" + nodes[0] + "/proxy/configz")
    ls_proxy.terminate()

    if (r.status_code != 200):
        sys.exit("Could not download kubeletconfig")
    config = r.json()['kubeletconfig']
    
    #manually add kind and api version
    config['kind'] = "KubeletConfiguration"
    config['apiVersion'] = "kubelet.config.k8s.io/v1beta1"
    return config


SCRIPT_PATH = os.path.dirname(__file__)

nodes = getNodes()
print(nodes)

#load configs and create final config
config = getKubeletConfig()
config_delta = json.load(open(SCRIPT_PATH + '/config.json'))
config_new = merge_two_dicts(config, config_delta)

#output new config
print("Final config")
print(json.dumps(config_new, indent=2))
with open(SCRIPT_PATH + '/out.json', 'w') as outfile:
    json.dump(config_new, outfile, indent=2)

# STOP IF NOT --confirm
if (not args.confirm):
    print("Config out.json created. Use --confirm to patch all nodes.")
    exit()

#create configmap
kc_name=""
print("Create ConfigMap for kubelet-config")
try:
    cm_output_text = os.popen("kubectl -n kube-system create configmap kubelet-config --from-file=kubelet=" + SCRIPT_PATH + "/out.json --append-hash -o json 2>&1").read()
    cm_output = json.loads(cm_output_text)
    if not 'metadata' in cm_output:
        sys.exit("Could not create configmap")
    kc_name = cm_output['metadata']['name']
except Exception:
    # config map exists - get name
    r1 = re.findall(r"kubelet\-config\-\w+", cm_output_text)
    if (len(r1) == 1):
        kc_name = r1[0]
        print("ConfigMap already exists: " + kc_name)
    else:
        print(cm_output_text)
    pass

#safety stop
if len(kc_name) < 5:
    sys.exit("Error: Could not get ConfigMap name")

#apply new config
print("Apply config to nodes")
for node in nodes:
    if args.time > 0:
        print("Sleeping " + str(args.time) + "s for stability reasons")
        time.sleep(args.time)
    os.system('kubectl patch node ' + node + ' -p "{\\"spec\\":{\\"configSource\\":{\\"configMap\\":{\\"name\\":\\"' + kc_name + '\\",\\"namespace\\":\\"kube-system\\",\\"kubeletConfigKey\\":\\"kubelet\\"}}}}"')