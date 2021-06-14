# KubeletConfiguration Patcher
Dieses Python3 Script patched KubeletConfiguration Settings auf alle Kubelets eines k8s Clusters.  
Grundlage: https://kubernetes.io/docs/tasks/administer-cluster/reconfigure-kubelet/  

## Hinweise 
Status: Experimental  
Es gibt noch kein Errorhandling falscher Configs!  
Benötigt Kubernetes > v1.11 beta  
  
```The kubelet's configz endpoint is there to help with debugging, and is not a stable part of kubelet behavior. Do not rely on the behavior of this endpoint for production scenarios or for use with automated tools.```  
Quelle: https://kubernetes.io/docs/tasks/administer-cluster/reconfigure-kubelet/


## Arbeitsweise
Das Skript lädt über einen kubectl proxy die aktuelle KubeletConfiguration eines Nodes herunter. Diese Config wird mit eigenen Einstellungen aus der config.json kombiniert und in einer ConfigMap gespeichert. Anschließend werden nacheinander alle Nodes mit der KubeletConfiguration gepatched.

## config.json
Hier können eigene KubeletConfiguration Settings gesetzt werden.   
Doku: https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/

## out.json
Diese Datei wird durch das Skript generiert und entspricht der neu generierten KubeletConfiguration. 
