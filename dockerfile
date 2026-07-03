FROM ros:humble
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /quac_ws/src
COPY ./thermalcv ./thermalcv
WORKDIR /quac_ws

RUN source /opt/ros/humble/setup.bash && colcon build

RUN echo "source /quac_ws/install/setup.bash" >> ~/.bashrc

CMD ["/bin/bash"]