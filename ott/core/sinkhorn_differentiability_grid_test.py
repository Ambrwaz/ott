# coding=utf-8
# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Tests for the Policy."""

from absl.testing import absltest
from absl.testing import parameterized
import jax
import jax.numpy as np
import jax.test_util
from ott.core import sinkhorn
from ott.core.ground_geometry import grid


class SinkhornGradGridTest(jax.test_util.JaxTestCase):

  def setUp(self):
    super().setUp()
    self.rng = jax.random.PRNGKey(0)

  @parameterized.parameters([True], [False])
  def test_autograd_sinkhorn_grid(self, lse_mode):
    """Test gradient w.r.t. probability weights."""
    eps = 1e-3  # perturbation magnitude
    keys = jax.random.split(self.rng, 3)
    grid_size = (2, 3, 4)
    a = jax.random.uniform(keys[0], grid_size) + 1.0
    b = jax.random.uniform(keys[1], grid_size) + 1.0
    a = a.ravel() / np.sum(a)
    b = b.ravel() / np.sum(b)
    geom = grid.Grid(grid_size=grid_size, epsilon=0.2)

    def reg_ot(a, b):
      return sinkhorn.sinkhorn(
          geom, a=a, b=b, threshold=0.1, lse_mode=lse_mode).reg_ot_cost

    reg_ot_and_grad = jax.jit(jax.value_and_grad(reg_ot))
    _, grad_reg_ot = reg_ot_and_grad(a, b)
    delta = jax.random.uniform(keys[2], grid_size).ravel()
    delta = delta - np.mean(delta)

    # center perturbation
    reg_ot_delta_plus = reg_ot(a + eps * delta, b)
    reg_ot_delta_minus = reg_ot(a - eps * delta, b)
    delta_dot_grad = np.sum(delta * grad_reg_ot)
    self.assertAllClose(delta_dot_grad,
                        (reg_ot_delta_plus - reg_ot_delta_minus) / (2 * eps),
                        rtol=1e-03, atol=1e-02)

  @parameterized.parameters([True], [False])
  def test_autograd_sinkhorn_x_grid(self, lse_mode):
    """Test gradient w.r.t. probability weights."""
    eps = 1e-3  # perturbation magnitude
    keys = jax.random.split(self.rng, 3)
    x = (np.array([.0, 1.0], dtype=np.float32),
         np.array([.3, .4, .7], dtype=np.float32),
         np.array([1.0, 1.3, 2.4, 3.7], dtype=np.float32))
    grid_size = tuple([xs.shape[0] for xs in x])
    a = jax.random.uniform(keys[0], grid_size) + 1.0
    b = jax.random.uniform(keys[1], grid_size) + 1.0
    a = a.ravel() / np.sum(a)
    b = b.ravel() / np.sum(b)
    geom = grid.Grid(x=x, epsilon=1.0)

    def reg_ot(a, b):
      return sinkhorn.sinkhorn(
          geom, a=a, b=b, threshold=0.1, lse_mode=lse_mode).reg_ot_cost

    reg_ot_and_grad = jax.jit(jax.value_and_grad(reg_ot))
    _, grad_reg_ot = reg_ot_and_grad(a, b)
    delta = jax.random.uniform(keys[2], grid_size).ravel()
    delta = delta - np.mean(delta)

    # center perturbation
    reg_ot_delta_plus = reg_ot(a + eps * delta, b)
    reg_ot_delta_minus = reg_ot(a - eps * delta, b)
    delta_dot_grad = np.sum(delta * grad_reg_ot)
    self.assertAllClose(delta_dot_grad,
                        (reg_ot_delta_plus - reg_ot_delta_minus) / (2 * eps),
                        rtol=1e-03, atol=1e-02)

  @parameterized.parameters([True], [False])
  def test_autograd_sinkhorn_x_grid_x_perturbation(self, lse_mode):
    """Test gradient w.r.t. probability weights."""
    eps = 1e-3  # perturbation magnitude
    keys = jax.random.split(self.rng, 6)
    x = (np.array([.0, 1.0]),
         np.array([.3, .4, .7]),
         np.array([1.0, 1.3, 2.4, 3.7]))
    grid_size = tuple([xs.shape[0] for xs in x])
    a = jax.random.uniform(keys[0], grid_size) + 1.0
    b = jax.random.uniform(keys[1], grid_size) + 1.0
    a = a.ravel() / np.sum(a)
    b = b.ravel() / np.sum(b)

    def reg_ot(x):
      geom = grid.Grid(x=x, epsilon=1.0)
      return sinkhorn.sinkhorn(
          geom, a=a, b=b, threshold=0.1, lse_mode=lse_mode).reg_ot_cost

    reg_ot_and_grad = jax.jit(jax.value_and_grad(reg_ot))
    _, grad_reg_ot = reg_ot_and_grad(x)
    delta = [jax.random.uniform(keys[i], (g,)) for i, g in enumerate(grid_size)]

    x_p_delta = [(xs + eps * delt) for xs, delt in zip(x, delta)]
    x_m_delta = [(xs - eps * delt) for xs, delt in zip(x, delta)]

    # center perturbation
    reg_ot_delta_plus = reg_ot(x_p_delta)
    reg_ot_delta_minus = reg_ot(x_m_delta)
    delta_dot_grad = np.sum(np.array(
        [np.sum(delt * gr, axis=None) for delt, gr in zip(delta, grad_reg_ot)]
        ))
    self.assertAllClose(delta_dot_grad,
                        (reg_ot_delta_plus - reg_ot_delta_minus) / (2 * eps),
                        rtol=1e-03, atol=1e-02)


if __name__ == '__main__':
  absltest.main()
