FROM python:3.8.16-slim-buster

# kubectl
RUN apt update && apt install -y gpg ca-certificates curl bash-completion apt-transport-https --no-install-recommends && apt clean
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
RUN mkdir /root/.kube

# kubectl autocomplete
RUN echo 'source /etc/bash_completion' >> ~/.bashrc
RUN echo 'source <(kubectl completion bash)' >>~/.bashrc
RUN echo 'alias k=kubectl' >>~/.bashrc
RUN echo 'complete -o default -F __start_kubectl k' >>~/.bashrc

# helm
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor > /usr/share/keyrings/helm.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" > /etc/apt/sources.list.d/helm-stable-debian.list
RUN apt update && apt install -y helm && apt clean

# go 
RUN curl -O https://go.dev/dl/go1.22.4.linux-amd64.tar.gz -L
RUN echo 'export PATH=$PATH:/usr/local/go/bin' >>~/.bashrc
RUN export PATH="$PATH:/usr/local/go/bin"

# cert-manager
RUN OS=$(go env GOOS); ARCH=$(go env GOARCH); curl -L -o cmctl.tar.gz https://github.com/cert-manager/cert-manager/releases/download/v1.14.6/cmctl-$OS-$ARCH.tar.gz
RUN tar xzf cmctl.tar.gz
RUN mv cmctl /usr/local/bin

# istioctl
RUN curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.22.1 TARGET_ARCH=x86_64 sh -
RUN export PATH="/root/istio-1.22.1/bin:$PATH"
RUN echo 'export PATH=/root/istio-1.22.1/bin:$PATH' >>~/.bashrc

# Apache ab tools for benchmark
RUN apt update && apt install -y apache2-utils --no-install-recommends && apt clean

# VIM, nano, iproute2, iputils-ping
RUN apt update && apt install -y vim nano iproute2 iputils-ping --no-install-recommends && apt clean

# welcome message
COPY welcome.sh /etc/profile.d
RUN chmod a+rx /etc/profile.d/welcome.sh
RUN echo "/etc/profile.d/welcome.sh" >> /root/.bashrc

# muBench software
RUN apt update; apt install -y git libpangocairo-1.0-0 --no-install-recommends; apt clean
COPY . /root/muBench
#WORKDIR /root
#RUN git clone https://github.com/mSvcBench/muBench.git
RUN pip3 install -r /root/muBench/requirements.txt

WORKDIR /root/muBench

CMD [ "sleep", "infinity"]