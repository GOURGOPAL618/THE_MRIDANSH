"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Module: 3_core_engine/models/spatiotemporal_backbone.py
Role: Production-Grade Spatiotemporal ConvLSTM Temporal Dynamics Backbone

Extracts and models temporal hydrological transitions (drying/wetting recession curves,
monsoon infiltration fronts, and rolling Kharif crop phenology) across multi-temporal
satellite observations while strictly preserving 2D spatial coordinate topology.

Key Features:
- Topology-preserving 2D Convolutional LSTM cell architecture.
- GroupNorm gate stabilization preventing vanishing/exploding gradients during BPTT.
- Dynamic temporal horizon support (arbitrary sequence length T >= 1).
- Autoregressive multi-step physical state rollout for satellite-gap forecasting.
- Pure PyTorch, zero external notebook dependencies, fully deterministic.
"""

from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvLSTMCell(nn.Module):
    """
    2D Convolutional LSTM Cell.
    
    Replaces matrix multiplications with 2D spatial convolutions, allowing
    temporal state recurrence while maintaining spatial neighborhood coordinates.
    """

    def __init__(self, in_channels: int, hidden_channels: int, kernel_size: int = 3):
        super(ConvLSTMCell, self).__init__()
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        padding = kernel_size // 2

        # Combined convolution for all 4 gates (input, forget, candidate, output)
        self.conv_gates = nn.Conv2d(
            in_channels + hidden_channels,
            4 * hidden_channels,
            kernel_size=kernel_size,
            padding=padding,
            bias=False,
        )
        self.gn = nn.GroupNorm(num_groups=min(8, 4 * hidden_channels), num_channels=4 * hidden_channels)

    def forward(
        self,
        x: torch.Tensor,
        state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for a single timestep t.

        Parameters:
        -----------
        x : torch.Tensor
            Input feature tensor of shape (B, in_channels, H, W).
        state : Optional[Tuple[torch.Tensor, torch.Tensor]]
            Tuple of (h_prev, c_prev), each of shape (B, hidden_channels, H, W).
            If None, initializes zero states.

        Returns:
        --------
        Tuple[torch.Tensor, torch.Tensor]:
            (h_next, c_next), each of shape (B, hidden_channels, H, W).
        """
        b, _, h, w = x.shape

        if state is None:
            h_prev = torch.zeros(b, self.hidden_channels, h, w, device=x.device, dtype=x.dtype)
            c_prev = torch.zeros(b, self.hidden_channels, h, w, device=x.device, dtype=x.dtype)
        else:
            h_prev, c_prev = state

        # Concatenate input and previous hidden state along channel dimension
        combined = torch.cat([x, h_prev], dim=1)
        gates = self.gn(self.conv_gates(combined))

        # Split into individual gates (i, f, c_candidate, o)
        i_gate, f_gate, c_cand, o_gate = torch.split(gates, self.hidden_channels, dim=1)

        i_t = torch.sigmoid(i_gate)
        f_t = torch.sigmoid(f_gate)
        c_cand = torch.tanh(c_cand)
        o_t = torch.sigmoid(o_gate)

        # Update cell state and hidden state
        c_next = f_t * c_prev + i_t * c_cand
        h_next = o_t * torch.tanh(c_next)

        return h_next, c_next


class SpatiotemporalBackbone(nn.Module):
    """
    Spatiotemporal ConvLSTM Temporal Dynamics Backbone (AETHER-MRID1607X).
    
    Processes multi-timestep satellite latent cubes (B, T, C, H, W) into an integrated
    temporal soil moisture manifold (B, C, H, W). Includes residual skip connections
    from the latest observation and autoregressive forward rollout capabilities.
    """

    def __init__(
        self,
        in_channels: int = 64,
        hidden_channels: int = 64,
        num_layers: int = 1,
        kernel_size: int = 3,
    ):
        super(SpatiotemporalBackbone, self).__init__()
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.num_layers = num_layers

        # Stacked ConvLSTM layers
        self.layers = nn.ModuleList()
        for i in range(num_layers):
            c_in = in_channels if i == 0 else hidden_channels
            self.layers.append(ConvLSTMCell(c_in, hidden_channels, kernel_size=kernel_size))

        # Residual spatiotemporal fusion projection
        self.residual_proj = nn.Sequential(
            nn.Conv2d(in_channels + hidden_channels, hidden_channels, kernel_size=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=hidden_channels),
            nn.GELU(),
            nn.Conv2d(hidden_channels, hidden_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=hidden_channels),
            nn.GELU(),
        )

        # Autoregressive transition head for forward rollout during satellite gaps
        self.rollout_transition = nn.Sequential(
            nn.Conv2d(hidden_channels, hidden_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=hidden_channels),
            nn.GELU(),
            nn.Conv2d(hidden_channels, hidden_channels, kernel_size=1),
        )

    def forward(
        self,
        sequence: torch.Tensor,
        return_all_timesteps: bool = False,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass through spatiotemporal sequence.

        Parameters:
        -----------
        sequence : torch.Tensor
            Input spatiotemporal tensor of shape (B, T, C, H, W).
        return_all_timesteps : bool
            If True, also returns full trajectory of hidden states across all T.

        Returns:
        --------
        Tuple[torch.Tensor, Dict[str, Any]]:
            - integrated_state : Tensor of shape (B, hidden_channels, H, W)
            - metadata : Diagnostic telemetry dictionary
        """
        if sequence.dim() != 5:
            raise ValueError(f"Expected 5D spatiotemporal tensor (B, T, C, H, W), got {sequence.dim()}D tensor.")

        b, t, c, h, w = sequence.shape
        if c != self.in_channels:
            raise ValueError(f"Channel mismatch: expected {self.in_channels}, got {c}.")

        current_inputs = sequence
        layer_outputs = []

        # Iterate over ConvLSTM layers
        for layer_idx, cell in enumerate(self.layers):
            h_state = None
            h_history = []

            for timestep in range(t):
                x_t = current_inputs[:, timestep]
                h_state = cell(x_t, h_state)
                h_history.append(h_state[0])

            current_inputs = torch.stack(h_history, dim=1)
            layer_outputs.append(current_inputs)

        # Final hidden state at timestep T-1 from last layer
        h_final = layer_outputs[-1][:, -1]  # (B, hidden_channels, H, W)

        # Latest observation slice from input sequence
        latest_obs = sequence[:, -1]  # (B, in_channels, H, W)

        # Residual skip connection combining dynamic memory + current satellite observation
        fused_state = self.residual_proj(torch.cat([h_final, latest_obs], dim=1))

        metadata = {
            "batch_size": b,
            "timesteps": t,
            "spatial_dim": (h, w),
            "hidden_channels": self.hidden_channels,
            "has_residual_skip": True,
        }

        if return_all_timesteps:
            metadata["full_trajectory"] = layer_outputs[-1]  # (B, T, hidden_channels, H, W)

        return fused_state, metadata

    def rollout_forecast(
        self,
        initial_state: torch.Tensor,
        steps: int = 3,
    ) -> List[torch.Tensor]:
        """
        Autoregressively roll out physical soil moisture state into future timesteps
        during satellite orbital pass gaps.

        Parameters:
        -----------
        initial_state : torch.Tensor
            Initial integrated state of shape (B, hidden_channels, H, W).
        steps : int
            Number of future timesteps to project forward.

        Returns:
        --------
        List[torch.Tensor]:
            List of forecasted state tensors, each of shape (B, hidden_channels, H, W).
        """
        forecasts = []
        curr = initial_state

        for step_idx in range(steps):
            delta = self.rollout_transition(curr)
            curr = curr + delta  # Euler-style residual step
            forecasts.append(curr)

        return forecasts
