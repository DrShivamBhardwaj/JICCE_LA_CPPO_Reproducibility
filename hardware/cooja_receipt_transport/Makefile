CONTIKI_PROJECT = receipt-transport
all: $(CONTIKI_PROJECT)
ifndef CONTIKI
$(error Set CONTIKI to your Contiki-NG source directory)
endif
override EXTRA_CC_ARGS += -include $(CURDIR)/native-compat.h
MAKE_MAC = MAKE_MAC_CSMA
MAKE_NET = MAKE_NET_NULLNET
PROJECT_SOURCEFILES += sha256.c monocypher.c monocypher-ed25519.c
PROJECTDIRS += ../cortex_m3_validation/vendor ../cortex_m3_validation/include
include $(CONTIKI)/Makefile.include
