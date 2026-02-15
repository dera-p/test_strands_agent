FROM public.ecr.aws/lambda/python:3.11

# 1. Update & Install Basic Tools
RUN yum update -y && \
    yum install -y \
    gzip \
    tar \
    xz \
    wget \
    unzip \
    yum-utils \
    shadow-utils \
    && yum clean all

# 2. Install Node.js 16 (Binary Install - GLIBC 2.17 compatible)
RUN cd /tmp && \
    wget https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz && \
    tar -xJvf node-v16.20.2-linux-x64.tar.xz && \
    cp -r node-v16.20.2-linux-x64/* /usr/ && \
    rm -rf /tmp/node-v*

# 3. Install Dependencies for Playwright & LibreOffice (Install BEFORE downloading RPMs)
RUN yum install -y \
    java-17-amazon-corretto-headless \
    alsa-lib \
    at-spi2-atk \
    at-spi2-core \
    atk \
    cups-libs \
    dbus-libs \
    dbus-glib \
    expat \
    libX11 \
    libXcomposite \
    libXdamage \
    libXext \
    libXfixes \
    libXrandr \
    libgbm \
    libdrm \
    libxkbcommon \
    mesa-libgbm \
    nss \
    pango \
    cairo \
    gtk3 \
    libGL \
    libXinerama \
    && yum clean all

# 4. Install LibreOffice (Download RPMs)
# URL: Using 25.2.7 (Verified available)
RUN cd /tmp && \
    wget https://download.documentfoundation.org/libreoffice/stable/25.2.7/rpm/x86_64/LibreOffice_25.2.7_Linux_x86-64_rpm.tar.gz && \
    tar -xvf LibreOffice_25.2.7_Linux_x86-64_rpm.tar.gz && \
    cd LibreOffice*_rpm/RPMS && \
    yum localinstall -y --nogpgcheck *.rpm && \
    rm -rf /tmp/LibreOffice*

# 5. Install Build Tools (for Python packages)
RUN yum install -y \
    gcc \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    python3-devel \
    && yum clean all

# 5. Set Environment Variables
ENV PYTHONUTF8=1
ENV HOME=/tmp
ENV PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers
# Add LibreOffice to path if not automatically added (usually /opt/libreoffice7.6/program/soffice)
ENV PATH="$PATH:/opt/libreoffice7.6/program"

# 6. Copy Project Files
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}
COPY agentskills/ ${LAMBDA_TASK_ROOT}/agentskills/
COPY skills/ ${LAMBDA_TASK_ROOT}/skills/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY my_tools.py ${LAMBDA_TASK_ROOT}
COPY my_pptx_agent.py ${LAMBDA_TASK_ROOT}
COPY setup.py ${LAMBDA_TASK_ROOT}

# 7. Install Python Dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir numpy==1.26.4
RUN pip install --no-cache-dir -r requirements-lambda.txt
RUN pip install --no-cache-dir .

# 8. Install Node.js Dependencies
WORKDIR ${LAMBDA_TASK_ROOT}
COPY package.json ${LAMBDA_TASK_ROOT}
RUN npm init -y && \
    npm install pptxgenjs playwright@1.38.0 react-icons sharp

# 9. Install Playwright Browsers (Chromium)
# We install dependencies via yum above, so we just install the browser binary here.
# --with-deps on AL2 might fail if it tries to use yum (which we did manually), so we try without first or verify
RUN npx playwright install chromium

# 10. Copy Handler
COPY agent_handler.py ${LAMBDA_TASK_ROOT}

# 11. Set CMD to Lambda handler
CMD [ "agent_handler.handler" ]

