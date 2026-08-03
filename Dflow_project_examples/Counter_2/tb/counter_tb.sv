`timescale 1ns/1ps

module counter_tb;
    logic clk;
    logic rst_n;
    logic [3:0] count;

    counter dut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    initial begin
        $dumpfile("sim/waves/counter.vcd");
        $dumpvars(0, counter_tb);

        clk = 1'b0;
        rst_n = 1'b0;
        #1;
        rst_n = 1'b1;
        #1;
        repeat (8) begin
            clk = 1'b1;
            #1;
            clk = 1'b0;
            #1;
        end

        if (count !== 4'd8) begin
            $display("FAIL: expected count 8, got %0d", count);
            $fatal(1);
        end

        $display("PASS: counter reached %0d", count);
        $finish;
    end
endmodule