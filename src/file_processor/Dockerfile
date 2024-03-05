FROM public.ecr.aws/lambda/python:3.11

RUN pip install --upgrade pip

# libsndfile is required to use PyAV, which is used to read in samples
RUN yum clean all
RUN yum install -y libsndfile
RUN rm -rf /var/cache/yum

COPY requirements.txt ./
RUN pip install -r requirements.txt --upgrade

COPY *.py ./

CMD ["main.lambda_handler"]