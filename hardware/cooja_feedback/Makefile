CONTIKI_PROJECT = feedback
all: $(CONTIKI_PROJECT)
ifndef CONTIKI
$(error Set CONTIKI)
endif
override EXTRA_CC_ARGS += -include $(CURDIR)/../cooja_receipt_transport/native-compat.h
MAKE_MAC = MAKE_MAC_CSMA
MAKE_NET = MAKE_NET_NULLNET
PROJECT_SOURCEFILES += sha256.c monocypher.c monocypher-ed25519.c
PROJECTDIRS += ../cortex_m3_validation/vendor ../cortex_m3_validation/include ../cc2538_q22
include $(CONTIKI)/Makefile.include
