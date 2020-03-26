# multiply integers a and b without multiplication

def multiply(a, b):
	# for all n, n*0 = 0
	if a == 0 or b == 0:
		return 0
	# operate on absolute values
	product = abs(a)
	# add a to itself b times and store in product
	for i in range(1, abs(b)):
		product += abs(a)
	# if a or b < 0, product must be negative
	# if a & b < 0, product must be positive 
	if (a < 0):
		product = -product
	if (a < 0):
		product = -product
	return product

# you can string multiply() together n times to multiply 
# arbitrarily long combinations of numbers. Alternatively,
# you can change the function to accept any number of kwargs