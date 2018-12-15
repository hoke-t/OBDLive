#include <stdio.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netinet/ether.h>
#include <linux/if_packet.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <linux/can.h>
#include <linux/can/raw.h>

#define PORT 31415 

unsigned char asc2nibble(char c) {
    if ((c >= '0') && (c <= '9'))
        return c - '0';

    if ((c >= 'A') && (c <= 'F'))
        return c - 'A' + 10;

    if ((c >= 'a') && (c <= 'f'))
        return c - 'a' + 10;

    return 0x0F; // error
}

int main(int argc, char const *argv[])
{
    int server_fd, server_socket, valread;
    struct sockaddr_in serveraddr;
    int opt = 1;
    int addrlen = sizeof(serveraddr);
    char buffer[32] = {0};

    int can_fd;
    struct sockaddr_can canaddr;
    struct can_filter rfilter[1];
    struct ifreq canifr;

    // Creating socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Forcefully attaching socket to the port 31415
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    serveraddr.sin_family = AF_INET;
    serveraddr.sin_addr.s_addr = INADDR_ANY;
    serveraddr.sin_port = htons(PORT);

    // Forcefully attaching socket to the port 31415
    if (bind(server_fd, (struct sockaddr *)&serveraddr, sizeof(serveraddr))<0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    if ((server_socket = accept(server_fd, (struct sockaddr *)&serveraddr, (socklen_t*)&addrlen)) < 0) {
        perror("accept");
        exit(EXIT_FAILURE);
    }

    // Setup CAN socket
    if ((can_fd = socket(PF_CAN, SOCK_RAW, CAN_RAW)) == 0) {
        perror("cansocket failed");
        exit(EXIT_FAILURE);
    }

    strcpy(canifr.ifr_name, "can0");
    ioctl(can_fd, SIOCGIFINDEX, &canifr);

    canaddr.can_family = AF_CAN;
    canaddr.can_ifindex = canifr.ifr_ifindex;

    if (bind(can_fd, (struct sockaddr *)&canaddr, sizeof(canaddr)) < 0) {
        perror("canNOT bind");
        exit(EXIT_FAILURE);
    } 

    // Only receive responses on $7e8
    rfilter[0].can_id = 0x7e8;
    rfilter[0].can_mask = CAN_SFF_MASK;
    setsockopt(can_fd, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter));

    while (1) {
        valread = read(server_socket, buffer, 32);
        //printf("Received: %s\n", buffer);

        char candata[32] = {0};

        strncat(candata, buffer, 16);

        struct can_frame frame;
        frame.can_id = 0x7df; // Diagnostic arbitration id

        int i;
        unsigned char tmp;
        for (i = 0; i < 8; i++) {
            if ((tmp = asc2nibble(candata[2*i])) > 0x0F)
                return -3;

            frame.data[i] = (tmp << 4);

            if ((tmp = asc2nibble(candata[2*i+1])) > 0x0F)
                return -2;

            frame.data[i] |= tmp;
        }

        frame.can_dlc = i; 

        int nbytes = write(can_fd, &frame, sizeof(struct can_frame));
        printf("Wrote %s to the bus (%d).\n", candata, nbytes);

        int awaiting_data = 1;
        int isotp_size = -1; // Used to store the size of the data, if it's an ISO-TP response.
        int frames_received = 0;

        while (awaiting_data) {
            nbytes = read(can_fd, &frame, sizeof(struct can_frame));

            char response[32] = {0};
            
            // Write bytes to hex in response
            for (i=0; i<8 && i<nbytes; i++) {
                sprintf(&response[i*2], "%02x", frame.data[i]);
            }

            printf("Read %s from the bus (First byte is %d raw).\n", response, frame.data[0]);
            
            // Send response to client
            send(server_socket, response, strlen(response), 0);

            // Assume we're not awaiting data, but correct this below if needed.
            awaiting_data = 0;

            // If it's ISO-TP, we need to save the size if it's the first frame.
            if ((frame.data[0] >> 4) == 1) {
                isotp_size = (frame.data[0] & 0xF) << 8 | frame.data[1];
                isotp_size -= 6;
                
                // Converts bytes to frames.
                if (isotp_size % 7 == 0) {
                    isotp_size /= 7;
                } else {
                    isotp_size /= 7;
                    isotp_size += 1;
                }

                printf("We've got ISO-TP on our hands... hold on tight. Expecting %d frames.\n", isotp_size);
            }
            
            // If it's ISO-TP, we need to keep reading if it's not the last consecutive frame
            if (frames_received++ < isotp_size) {
                awaiting_data = 1;

                // Send a flow control frame that basically says send everything w/o flow control. (https://en.wikipedia.org/wiki/ISO_15765-2)
                struct can_frame flowframe;
                flowframe.can_id = 0x7e8 - 8; // Diagnostic arbitration response id

                flowframe.data[0] = 0b00110000; // This is a flow control message, continue to send.
                flowframe.data[1] = 0;          // Don't delay.
                flowframe.data[2] = 10;         // Wait 10 ms per frame

                flowframe.can_dlc = 8;

                write(can_fd, &flowframe, sizeof(struct can_frame));
                printf("Sent that flow frame.\n");
            }
        }

    }

    return 0;
}
