FROM alpine:latest

# Install kubectl
RUN apk add --no-cache curl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl

# Add the script
COPY label-nodes.sh /label-nodes.sh
RUN chmod +x /label-nodes.sh

CMD ["/label-nodes.sh"]
