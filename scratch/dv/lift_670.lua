-- coderabbit-ai-generated:v1
-- Conditional static reconstruction of prototype 670.
-- The supplied rounds and finish functions represent captured upvalues.
-- Reachability, argument origins, round indices and equivalence remain unverified.
local function read_word(bytes, offset)
  return bytes[offset + 1]
    + bytes[offset + 2] * 256
    + bytes[offset + 3] * 65536
    + bytes[offset + 4] * 16777216
end

return function(input, key_bytes, params, fourth_argument, rounds, finish)
  local state = { 0x61707865, 0x3320646e, 0x79622d32, 0x6b206574 }
  for i = 1, 8 do
    state[i + 4] = read_word(key_bytes, 4 * (i - 1))
  end
  for i = 1, 3 do
    state[i + 13] = read_word(params, 4 * (i - 1))
  end
  local round_count = params[13]
  local size = buffer.len(input)
  local output = buffer.create(size)
  local counter = 0

  for offset = 0, size - 1, 64 do
    state[13] = counter
    counter = counter + 1
    local work = {}
    for i = 1, 16 do
      work[i] = state[i]
    end
    rounds(work, round_count)

    local count = math.min(64, size - offset)
    local full_words = math.floor(count / 4)
    for i = 0, full_words - 1 do
      local word = bit32.band(work[i + 1] + state[i + 1], 0xffffffff)
      local pos = offset + i * 4
      buffer.writeu32(output, pos, bit32.bxor(buffer.readu32(input, pos), word))
    end
    if full_words * 4 < count then
      local word = work[full_words + 1] + state[full_words + 1]
      for i = 0, count - full_words * 4 - 1 do
        local pos = offset + full_words * 4 + i
        local byte = bit32.band(bit32.rshift(word, i * 8), 255)
        buffer.writeu8(output, pos, bit32.bxor(buffer.readu8(input, pos), byte))
      end
    end
  end
  local result = finish(output, fourth_argument)
  return result
end
