library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity blinker is
  port (clk : in std_logic; led : out std_logic);
end entity;

architecture rtl of blinker is
  signal counter : unsigned(26 downto 0) := (others => '0');
begin
  registers : process (clk)
  begin
    if rising_edge(clk) then
      counter <= counter + 1;
    end if;
  end process;
  led <= counter(counter'high);
end architecture;
