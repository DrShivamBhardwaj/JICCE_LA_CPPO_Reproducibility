ENTRY(Reset_Handler)
MEMORY { FLASH (rx) : ORIGIN = 0x00200000, LENGTH = 512K
         RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 32K }
SECTIONS {
 .vectors : { KEEP(*(.vectors)) } > FLASH
 .text : { *(.text*) *(.rodata*) } > FLASH
 .data : { *(.data*) } > RAM AT>FLASH
 .bss : { *(.bss*) *(COMMON) } > RAM
 /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
