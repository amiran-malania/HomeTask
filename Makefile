CC = gcc
CFLAGS = -fPIC -I./fio -Wall -O3
LDFLAGS = -shared -rdynamic -undefined dynamic_lookup
TARGET = the_best_protocol_ever.dylib
SRC = the_best_protocol_ever.c

FIO_DIR = fio
FIO_REPO = https://github.com/axboe/fio.git

.PHONY: all run clean clean-all tune-mac

all: $(TARGET)

# --- System Tuning ---
# Might be required to run this first
tune-mac:
	@echo "=> Applying macOS shared memory tuning (requires sudo)..."
	sudo sysctl -w kern.sysv.shmmax=52428800
	sudo sysctl -w kern.sysv.shmall=12800
	sudo sysctl -w kern.sysv.shmmni=128
	sudo sysctl -w kern.sysv.shmseg=32
	@echo "=> Tuning complete."

# --- 1. Clone the FIO Repository ---
$(FIO_DIR):
	@echo "=> Cloning FIO repository..."
	git clone $(FIO_REPO) $(FIO_DIR)

# --- 2. Configure and Build FIO ---
$(FIO_DIR)/fio: | $(FIO_DIR)
	@echo "=> Configuring and building FIO..."
	cd $(FIO_DIR) && ./configure
	$(MAKE) -C $(FIO_DIR)

# --- 3. Build the Custom Engine ---
$(TARGET): $(SRC) $(FIO_DIR)/fio
	@echo "=> Building custom IO engine..."
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(SRC)

run: $(TARGET)
	python3 protocol_stress_test.py

clean:
	rm -f *.bin $(TARGET) *.o

clean-all: clean
	rm -rf $(FIO_DIR)