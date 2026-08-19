module counter_formal;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    wire [3:0] count;

    counter dut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    // Turn the formal engine's global timestep into a regular design clock.
    always @($global_clock) begin
        clk <= !clk;
        if (!rst_n)
            rst_n <= 1'b1;
    end

    reg past_valid = 1'b0;
    always @(posedge clk) begin
        past_valid <= 1'b1;

        if (!rst_n)
            assert(count == 4'd0);

        if (past_valid && rst_n && $past(rst_n))
            assert(count == $past(count) + 1'b1);

`ifdef INTENTIONAL_FAILURE
        // Demonstration only: the counter must increment, so this deliberately
        // false claim produces a short counterexample waveform.
        if (past_valid && rst_n && $past(rst_n))
            assert(count == 4'd0);
`endif

        cover(rst_n && count == 4'hf);
    end
endmodule
